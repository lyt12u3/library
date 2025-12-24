# reader_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Reader Microservice")

# --- 1. ШАР DTO (Data Transfer Objects) ---
# [cite_start]Моделі для обміну даними між шарами та сервісами [cite: 2720]

class ReaderCreateDTO(BaseModel):
    id: int
    name: str

class ReaderReadDTO(BaseModel):
    id: int
    name: str
    status: str  # "active" або "blocked"

# --- 2. ШАР REPOSITORY (Data Layer) ---
# [cite_start]Відповідає за збереження та пошук даних в ізольованій БД [cite: 2720]

class ReaderRepository:
    def __init__(self):
        # Імітація власної БД мікросервісу (ізольована від інших сервісів)
        self._db = [
            {"id": 12, "name": "Інокентій Вармілов", "status": "active"},
            {"id": 13, "name": "Владислав Богуславський", "status": "active"}
        ]

    def get_all(self):
        return self._db

    def get_by_id(self, r_id: int):
        return next((r for r in self._db if r["id"] == r_id), None)

    def save(self, data: dict):
        self._db.append(data)
        return data

    def update_status_in_db(self, r_id: int, new_status: str):
        reader = self.get_by_id(r_id)
        if reader:
            reader["status"] = new_status
            return reader
        return None

repo = ReaderRepository()

# --- 3. ШАР SERVICE (Business Logic Layer) ---
# [cite_start]Містить логіку перевірок та валідації [cite: 2720]

class ReaderBusinessService:
    @staticmethod
    def list_all() -> List[ReaderReadDTO]:
        return [ReaderReadDTO(**r) for r in repo.get_all()]

    @staticmethod
    def find_one(r_id: int) -> ReaderReadDTO:
        data = repo.get_by_id(r_id)
        if not data:
            raise HTTPException(status_code=404, detail="Reader not found")
        return ReaderReadDTO(**data)

    @staticmethod
    def register_new(dto: ReaderCreateDTO) -> ReaderReadDTO:
        # Бізнес-перевірка: чи не зайнятий ID іншим читачем
        if repo.get_by_id(dto.id):
            raise HTTPException(status_code=400, detail="Reader with this ID already registered")
        
        new_reader = dto.dict()
        new_reader["status"] = "active" # За замовчуванням новий читач активний
        return ReaderReadDTO(**repo.save(new_reader))

    @staticmethod
    def change_status(r_id: int, status: str) -> ReaderReadDTO:
        if status not in ["active", "blocked"]:
            raise HTTPException(status_code=400, detail="Invalid status. Use 'active' or 'blocked'")
        
        updated = repo.update_status_in_db(r_id, status)
        if not updated:
            raise HTTPException(status_code=404, detail="Reader not found")
        return ReaderReadDTO(**updated)

# --- 4. ШАР CONTROLLER (API Layer) ---
# [cite_start]Обробка вхідних HTTP-запитів [cite: 2720]

@app.get("/readers", response_model=List[ReaderReadDTO])
def list_readers():
    """5. [Reader] Список всіх читачів"""
    return ReaderBusinessService.list_all()

@app.get("/readers/{id}", response_model=ReaderReadDTO)
def get_reader(id: int):
    """6. [Reader] Дані читача за ID"""
    return ReaderBusinessService.find_one(id)

@app.post("/readers", response_model=ReaderReadDTO)
def create_reader(dto: ReaderCreateDTO):
    """7. [Reader] Реєстрація читача"""
    return ReaderBusinessService.register_new(dto)

@app.put("/readers/{id}/status", response_model=ReaderReadDTO)
def update_status(id: int, status: str):
    """8. [Reader] Змінити статус читача"""
    return ReaderBusinessService.change_status(id, status)

if __name__ == "__main__":
    # Запуск мікросервісу на порту 8002
    uvicorn.run(app, host="127.0.0.1", port=8002)