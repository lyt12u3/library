from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Catalog Microservice")

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
            {"id": 101, "title": "Python HPC", "author": "Boguslavky Vlad", "description": "Variant 12", "available": True},
            {"id": 102, "title": "Clean Code", "author": "Robert Martin", "description": "Best practices", "available": True}
        ]

    def get_all(self):
        return self._db

    def get_by_id(self, book_id: int):
        return next((b for b in self._db if b["id"] == book_id), None)

    def find_by_author(self, author: str):
        return [b for b in self._db if author.lower() in b["author"].lower()]

    def save(self, data: dict):
        self._db.append(data)
        return data

    def update_availability(self, book_id: int, status: bool):
        book = self.get_by_id(book_id)
        if book:
            book["available"] = status
            return book
        return None

repo = BookRepository()

# --- 3. ШАР SERVICE (Business Logic Layer) --- 
class CatalogService:
    @staticmethod
    def list_books() -> List[BookReadDTO]:
        return [BookReadDTO(**b) for b in repo.get_all()]

    @staticmethod
    def get_details(book_id: int) -> BookReadDTO:
        data = repo.get_by_id(book_id)
        if not data: raise HTTPException(status_code=404, detail="Book not found")
        return BookReadDTO(**data)

    @staticmethod
    def search(author: str) -> List[BookReadDTO]:
        return [BookReadDTO(**b) for b in repo.find_by_author(author)]

    @staticmethod
    def add(dto: BookCreateDTO) -> BookReadDTO:
        if repo.get_by_id(dto.id):
            raise HTTPException(status_code=400, detail="ID already exists")
        new_book = dto.dict()
        new_book["available"] = True
        return BookReadDTO(**repo.save(new_book))

# --- 4. ШАР CONTROLLER (API Layer) --- 
@app.get("/catalog/books", response_model=List[BookReadDTO])
def get_all_books():
    return CatalogService.list_books()

@app.get("/catalog/books/{id}", response_model=BookReadDTO)
def get_book_by_id(id: int):
    return CatalogService.get_details(id)

@app.get("/catalog/books/search/{author}", response_model=List[BookReadDTO])
def find_books_by_author(author: str):
    return CatalogService.search(author)

@app.post("/catalog/books", response_model=BookReadDTO)
def add_book(dto: BookCreateDTO):
    return CatalogService.add(dto)

@app.put("/catalog/books/{id}/status")
def update_book_status(id: int, available: bool):
    updated = repo.update_availability(id, available)
    if not updated: raise HTTPException(status_code=404)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)