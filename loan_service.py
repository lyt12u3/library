# loan_service.py
import httpx
import asyncio
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn
import random

# --- ІНФРАСТРУКТУРНІ НАСТРОЙКИ (PZ4) ---
SERVICE_NAME = "loans"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8003
DISCOVERY_URL = "http://127.0.0.1:8000"

# --- 1. ШАР DTO ---
class LoanCreateDTO(BaseModel):
    bookId: int
    readerId: int

class LoanReadDTO(BaseModel):
    id: int
    bookId: int
    readerId: int
    status: str  # "active" або "returned"

# --- 2. ШАР REPOSITORY ---
class LoanRepository:
    def __init__(self):
        self._db = []

    def save(self, data: dict):
        data["id"] = len(self._db) + 1
        data["status"] = "active"
        self._db.append(data)
        return data

    def get_by_id(self, lid: int):
        return next((l for l in self._db if l["id"] == lid), None)

    def get_by_reader(self, rid: int):
        return [l for l in self._db if l["readerId"] == rid]

    def get_all_active(self):
        return [l for l in self._db if l["status"] == "active"]

repo = LoanRepository()

# --- 3. ШАР SERVICE (Динамічне виявлення та Логіка) ---
class LoanBusinessService:
    @staticmethod
    async def get_service_url(logic_name: str):
        """
        Реалізація критерію 'Рефакторинг виклику': 
        отримання адреси за логічним ім'ям через Discovery.
        """
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{DISCOVERY_URL}/services/{logic_name}")
                instances = resp.json()
                if not instances:
                    raise HTTPException(status_code=503, detail=f"Сервіс {logic_name} не знайдено в реєстрі")
                
                # Балансування навантаження на стороні клієнта 
                instance = random.choice(instances)
                return f"http://{instance['host']}:{instance['port']}"
            except Exception as e:
                if isinstance(e, HTTPException): raise e
                raise HTTPException(status_code=503, detail="Discovery Service недоступний")

    @staticmethod
    async def issue_book(dto: LoanCreateDTO):
        """9. [Loan] Оформити видачу книги (Оркестрація)"""
        
        # 1. Знаходимо Reader Service динамічно
        reader_api = await LoanBusinessService.get_service_url("readers")
        r_resp = requests.get(f"{reader_api}/readers/{dto.readerId}")
        
        if r_resp.status_code != 200 or r_resp.json()["status"] != "active":
            raise HTTPException(status_code=400, detail="Читач заблокований або не існує")

        # 2. Знаходимо Catalog Service динамічно
        catalog_api = await LoanBusinessService.get_service_url("catalog")
        b_resp = requests.get(f"{catalog_api}/catalog/books/{dto.bookId}")
        
        if b_resp.status_code != 200 or not b_resp.json()["available"]:
            raise HTTPException(status_code=400, detail="Книга недоступна")

        # 3. Реєстрація видачі
        loan = repo.save(dto.dict())
        
        # 4. Оновлення статусу книги в каталозі
        requests.put(f"{catalog_api}/catalog/books/{dto.bookId}/status", params={"available": False})
        
        return loan

# --- 4. ІНФРАСТРУКТУРНА ЛОГІКА (Discovery & Heartbeat) ---
async def send_heartbeat():
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
            print(f"[{SERVICE_NAME}] Успішно зареєстровано")
        except Exception as e:
            print(f"[{SERVICE_NAME}] Помилка реєстрації: {e}")
    
    heartbeat_task = asyncio.create_task(send_heartbeat())
    yield
    heartbeat_task.cancel()

app = FastAPI(title="Loan Microservice (PZ4 Orchestrator)", lifespan=lifespan)

# --- 5. ШАР CONTROLLER (API Endpoints) ---
@app.post("/loans", status_code=201)
async def create_loan(dto: LoanCreateDTO):
    return await LoanBusinessService.issue_book(dto)

@app.put("/loans/{id}/return")
async def return_book(id: int):
    """10. [Loan] Повернути книгу"""
    loan = repo.get_by_id(id)
    if not loan or loan["status"] == "returned":
        raise HTTPException(status_code=404, detail="Активний запис не знайдено")
    
    catalog_api = await LoanBusinessService.get_service_url("catalog")
    loan["status"] = "returned"
    requests.put(f"{catalog_api}/catalog/books/{loan['bookId']}/status", params={"available": True})
    return {"message": "Книгу успішно повернуто"}

@app.get("/loans/history/{reader_id}")
def get_history(reader_id: int):
    """11. [Loan] Історія запозичень читача"""
    return repo.get_by_reader(reader_id)

@app.get("/loans/active")
def get_active():
    """12. [Loan] Список книг на руках"""
    return repo.get_all_active()

if __name__ == "__main__":
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)