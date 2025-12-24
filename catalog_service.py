# catalog_service.py
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn

# --- КОНФІГУРАЦІЯ (PZ4 Requirement) ---
SERVICE_NAME = "catalog"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8001
DISCOVERY_URL = "http://127.0.0.1:8000"

# --- 1. ШАР DTO (Data Transfer Objects) ---
class BookCreateDTO(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str] = None

class BookReadDTO(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str] = None
    available: bool

# --- 2. ШАР REPOSITORY (Data Layer) ---
class BookRepository:
    def __init__(self):
        self._db = [
            {"id": 101, "title": "Python HPC", "author": "Boguslavsky Vlad", "description": "Variant 12", "available": True},
            {"id": 102, "title": "Clean Code", "author": "Robert Martin", "description": "Architecture", "available": True}
        ]

    def get_all(self): return self._db
    def get_by_id(self, b_id): return next((b for b in self._db if b["id"] == b_id), None)
    def find_by_author(self, author): return [b for b in self._db if author.lower() in b["author"].lower()]
    def save(self, data): self._db.append(data); return data
    def update_availability(self, b_id, status):
        book = self.get_by_id(b_id)
        if book: book["available"] = status; return book
        return None

repo = BookRepository()

# --- 3. ШАР SERVICE (Business Logic Layer) ---
class CatalogBusinessLogic:
    @staticmethod
    def list_books(): return [BookReadDTO(**b) for b in repo.get_all()]
    
    @staticmethod
    def add(dto: BookCreateDTO):
        if repo.get_by_id(dto.id): 
            raise HTTPException(status_code=400, detail="ID вже зайнятий")
        new_book = dto.dict()
        new_book["available"] = True
        return BookReadDTO(**repo.save(new_book))

# --- 4. ІНФРАСТРУКТУРНА ЛОГІКА (Discovery & Lifespan) ---
async def send_heartbeat():
    """Реалізація Heartbeat механізму для Discovery Service """
    while True:
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{DISCOVERY_URL}/heartbeat/{SERVICE_NAME}", 
                                 params={"host": SERVICE_HOST, "port": SERVICE_PORT})
            except Exception: pass
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Реєстрація при запуску 
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{DISCOVERY_URL}/register", 
                             params={"name": SERVICE_NAME, "host": SERVICE_HOST, "port": SERVICE_PORT})
            print(f"[{SERVICE_NAME}] Успішно зареєстровано в Discovery")
        except Exception as e:
            print(f"[{SERVICE_NAME}] Помилка реєстрації: {e}")
    
    # Запуск фонового завдання Heartbeat
    heartbeat_task = asyncio.create_task(send_heartbeat())
    yield
    # Зупинка Heartbeat при виключенні
    heartbeat_task.cancel()

app = FastAPI(title="Catalog Microservice (PZ4)", lifespan=lifespan)

# --- 5. ШАР CONTROLLER (API Endpoints) ---
@app.get("/catalog/books", response_model=List[BookReadDTO])
def get_all_books():
    """1. [Catalog] Показати всі книги"""
    return CatalogBusinessLogic.list_books()

@app.get("/catalog/books/{id}", response_model=BookReadDTO)
def get_book_by_id(id: int):
    """2. [Catalog] Пошук за ID книги"""
    data = repo.get_by_id(id)
    if not data: raise HTTPException(status_code=404, detail="Книгу не знайдено")
    return BookReadDTO(**data)

@app.get("/catalog/books/search/{author}", response_model=List[BookReadDTO])
def find_books_by_author(author: str):
    """3. [Catalog] Пошук за автором"""
    return [BookReadDTO(**b) for b in repo.find_by_author(author)]

@app.post("/catalog/books", response_model=BookReadDTO)
def add_book(dto: BookCreateDTO):
    """4. [Catalog] Додати нову книгу"""
    return CatalogBusinessLogic.add(dto)

@app.put("/catalog/books/{id}/status")
def update_book_status(id: int, available: bool):
    """Службовий метод для зміни статусу (викликається Loan Service)"""
    updated = repo.update_availability(id, available)
    if not updated: raise HTTPException(status_code=404)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)