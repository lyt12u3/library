from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Library Management System - Monolith")

# --- 1. МОДЕЛІ ДАНИХ (Pydantic Models) --- [cite: 739-758]
class Book(BaseModel):
    id: int
    title: str
    author: str
    description: Optional[str] = None
    available: bool = True

class Reader(BaseModel):
    id: int
    name: str
    status: str = "active"  # active, blocked

class Loan(BaseModel):
    id: int
    bookId: int
    readerId: int
    status: str = "active"  # active, returned

# --- 2. ІМІТАЦІЯ БАЗИ ДАНИХ (Fake DB) --- [cite: 661-698, 759-783]
books_db: List[dict] = [
    {"id": 1, "title": "The Witcher", "author": "A. Sapkowski", "description": "Fantasy novel", "available": True},
    {"id": 2, "title": "Clean Code", "author": "R. Martin", "description": "Programming guide", "available": True},
    {"id": 3, "title": "Python HPC", "author": "A. Yakhyaev", "description": "HPC Guide", "available": True}
]

readers_db: List[dict] = [
    {"id": 1, "name": "Arsen Yakhyaev", "status": "active"},
    {"id": 2, "name": "Vladyslav Bohuslavskyi", "status": "active"}
]

loans_db: List[dict] = []

# --- 3. CATALOG SERVICE ROUTER --- [cite: 784-819]
catalog_router = APIRouter(prefix="/catalog", tags=["Catalog"])

@catalog_router.get("/books", response_model=List[dict])
def get_all_books():
    """Отримати список усіх книг"""
    return books_db

@catalog_router.get("/books/{id}")
def get_book_by_id(id: int):
    """Отримати детальну інформацію про книгу"""
    for book in books_db:
        if book["id"] == id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")

@catalog_router.get("/books/search/{author_name}")
def find_books_by_author(author_name: str):
    """Пошук книг за автором"""
    results = [b for b in books_db if author_name.lower() in b["author"].lower()]
    return results

@catalog_router.post("/books")
def add_book(book: Book):
    """Додати нову книгу до каталогу"""
    books_db.append(book.dict())
    return book

# --- 4. READER SERVICE ROUTER --- [cite: 842-869]
reader_router = APIRouter(prefix="/readers", tags=["Readers"])

@reader_router.get("")
def get_all_readers():
    """Список усіх зареєстрованих читачів"""
    return readers_db

@reader_router.get("/{id}")
def get_reader_by_id(id: int):
    """Отримати дані про конкретного читача"""
    for reader in readers_db:
        if reader["id"] == id:
            return reader
    raise HTTPException(status_code=404, detail="Reader not found")

@reader_router.post("")
def register_reader(reader: Reader):
    """Реєстрація нового читача"""
    readers_db.append(reader.dict())
    return reader

@reader_router.put("/{id}/status")
def update_reader_status(id: int, status: str):
    """Оновити статус читача (active/blocked)"""
    for reader in readers_db:
        if reader["id"] == id:
            reader["status"] = status
            return reader
    raise HTTPException(status_code=404, detail="Reader not found")

# --- 5. LOAN SERVICE ROUTER (Logic & Interaction) --- [cite: 699-733]
loan_router = APIRouter(prefix="/loans", tags=["Loans"])

@loan_router.post("")
def create_loan(bookId: int, readerId: int):
    """Оформити видачу книги читачу"""
    # 1. Перевірка книги
    book = next((b for b in books_db if b["id"] == bookId), None)
    if not book or not book["available"]:
        raise HTTPException(status_code=400, detail="Book is not available or not found")
    
    # 2. Перевірка читача
    reader = next((r for r in readers_db if r["id"] == readerId), None)
    if not reader or reader["status"] != "active":
        raise HTTPException(status_code=400, detail="Reader is blocked or not found")
    
    # 3. Створення запису
    new_id = len(loans_db) + 1
    new_loan = {"id": new_id, "bookId": bookId, "readerId": readerId, "status": "active"}
    
    # 4. Оновлення статусу книги
    book["available"] = False
    loans_db.append(new_loan)
    return new_loan

@loan_router.put("/{loan_id}/return")
def return_book(loan_id: int):
    """Зафіксувати повернення книги"""
    for loan in loans_db:
        if loan["id"] == loan_id and loan["status"] == "active":
            loan["status"] = "returned"
            # Робимо книгу знову доступною
            for book in books_db:
                if book["id"] == loan["bookId"]:
                    book["available"] = True
            return {"message": "Book returned successfully"}
    raise HTTPException(status_code=404, detail="Active loan not found")

@loan_router.get("/history/{reader_id}")
def get_reader_history(reader_id: int):
    """Отримати історію всіх запозичень читача"""
    return [l for l in loans_db if l["readerId"] == reader_id]

@loan_router.get("/active")
def get_active_loans():
    """Список книг, які зараз на руках"""
    return [l for l in loans_db if l["status"] == "active"]

# Підключення всіх роутерів до застосунку [cite: 734, 869]
app.include_router(catalog_router)
app.include_router(reader_router)
app.include_router(loan_router)