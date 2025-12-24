# loan_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import uvicorn

# Імпорт конфігурації мережі
from config import CATALOG_SERVICE_URL, READER_SERVICE_URL

app = FastAPI(title="Loan Microservice (Orchestrator)")

# --- 1. ШАР DTO (Data Transfer Objects) --- 
# Міжсервісні та внутрішні моделі даних

class LoanCreateDTO(BaseModel):
    bookId: int
    readerId: int

class LoanReadDTO(BaseModel):
    id: int
    bookId: int
    readerId: int
    status: str  # "active" або "returned"

# --- 2. ШАР REPOSITORY (Data Layer) --- 
# Управління власною ізольованою базою даних видач

class LoanRepository:
    def __init__(self):
        # БД замовлень/видач, доступна тільки цьому сервісу
        self._db = []

    def save(self, loan_data: dict):
        loan_data["id"] = len(self._db) + 1
        loan_data["status"] = "active"
        self._db.append(loan_data)
        return loan_data

    def get_by_id(self, loan_id: int):
        return next((l for l in self._db if l["id"] == loan_id), None)

    def get_by_reader(self, reader_id: int):
        return [l for l in self._db if l["readerId"] == reader_id]

    def get_all_active(self):
        return [l for l in self._db if l["status"] == "active"]

repo = LoanRepository()

# --- 3. ШАР SERVICE (Business Logic Layer) --- 
# Оркестрація викликів до інших сервісів (IPC) та бізнес-логіка

class LoanBusinessService:
    @staticmethod
    def create_loan(dto: LoanCreateDTO) -> LoanReadDTO:
        """9. [Loan] Оформити видачу книги читачу"""
        
        # Критерій: Реалізовано синхронний виклик (REST over HTTP) 
        # 1. Перевірка читача у Reader Service
        try:
            r_resp = requests.get(f"{READER_SERVICE_URL}/readers/{dto.readerId}")
            if r_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Reader not found in Reader Service")
            
            reader = r_resp.json()
            if reader["status"] != "active":
                raise HTTPException(status_code=400, detail="Reader is blocked")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Reader Service is unavailable")

        # 2. Перевірка книги у Catalog Service
        try:
            b_resp = requests.get(f"{CATALOG_SERVICE_URL}/catalog/books/{dto.bookId}")
            if b_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Book not found in Catalog")
            
            book = b_resp.json()
            if not book["available"]:
                raise HTTPException(status_code=400, detail="Book is already loaned")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Catalog Service is unavailable")

        # 3. Збереження видачі у локальну БД
        new_loan = repo.save(dto.dict())

        # 4. Зміна статусу книги у Catalog Service (Side Effect)
        requests.put(f"{CATALOG_SERVICE_URL}/catalog/books/{dto.bookId}/status", params={"available": False})
        
        return LoanReadDTO(**new_loan)

    @staticmethod
    def return_loan(loan_id: int):
        """10. [Loan] Повернути книгу"""
        loan = repo.get_by_id(loan_id)
        if not loan or loan["status"] == "returned":
            raise HTTPException(status_code=404, detail="Active loan record not found")

        # Оновлення статусу в локальній БД
        loan["status"] = "returned"

        # Повернення книги в доступ у Catalog Service
        requests.put(f"{CATALOG_SERVICE_URL}/catalog/books/{loan['bookId']}/status", params={"available": True})
        
        return {"message": "Book successfully returned"}

# --- 4. ШАР CONTROLLER (API Layer) --- 

@app.post("/loans", response_model=LoanReadDTO, status_code=201)
def create_loan(dto: LoanCreateDTO):
    """Оформити видачу (Оркестрація через Catalog та Reader)"""
    return LoanBusinessService.create_loan(dto)

@app.put("/loans/{id}/return")
def return_book(id: int):
    """Зафіксувати повернення книги"""
    return LoanBusinessService.return_loan(id)

@app.get("/loans/history/{reader_id}", response_model=List[LoanReadDTO])
def get_reader_history(reader_id: int):
    """11. [Loan] Історія запозичень читача"""
    history = repo.get_by_reader(reader_id)
    return [LoanReadDTO(**l) for l in history]

@app.get("/loans/active", response_model=List[LoanReadDTO])
def get_active_loans():
    """12. [Loan] Список книг на руках (активні)"""
    active = repo.get_all_active()
    return [LoanReadDTO(**l) for l in active]

if __name__ == "__main__":
    # Запуск мікросервісу на порту 8003
    uvicorn.run(app, host="127.0.0.1", port=8003)