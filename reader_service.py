# reader_service.py
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn

# --- ИНФРАСТРУКТУРНЫЕ НАСТРОЙКИ (PZ4) ---
SERVICE_NAME = "readers"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8002
DISCOVERY_URL = "http://127.0.0.1:8000"

# --- 1. ШАР DTO (Data Transfer Objects) ---
#  Использование DTO для передачи данных
class ReaderCreateDTO(BaseModel):
    id: int
    name: str

class ReaderReadDTO(BaseModel):
    id: int
    name: str
    status: str  # "active" или "blocked"

# --- 2. ШАР REPOSITORY (Data Layer) ---
#  Изолированная база данных микросервиса
class ReaderRepository:
    def __init__(self):
        self._db = [
            {"id": 12, "name": "Артемій Василенко", "status": "active"},
            {"id": 13, "name": "Владислав Богуславский", "status": "active"}
        ]

    def get_all(self):
        return self._db

    def get_by_id(self, r_id: int):
        return next((r for r in self._db if r["id"] == r_id), None)

    def add(self, data: dict):
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
class ReaderBusinessService:
    @staticmethod
    def get_reader(r_id: int) -> ReaderReadDTO:
        data = repo.get_by_id(r_id)
        if not data:
            raise HTTPException(status_code=404, detail="Читатель не найден")
        return ReaderReadDTO(**data)

    @staticmethod
    def register(dto: ReaderCreateDTO) -> ReaderReadDTO:
        if repo.get_by_id(dto.id):
            raise HTTPException(status_code=400, detail="ID уже зарегистрирован")
        new_data = dto.dict()
        new_data["status"] = "active"
        return ReaderReadDTO(**repo.add(new_data))

# --- 4. ИНФРАСТРУКТУРНАЯ ЛОГИКА (Discovery & Heartbeat) ---
#  Автоматизация конфигурации и Heartbeat
async def send_heartbeat():
    while True:
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{DISCOVERY_URL}/heartbeat/{SERVICE_NAME}", 
                                 params={"host": SERVICE_HOST, "port": SERVICE_PORT})
            except Exception:
                pass
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    #  Автоматическая регистрация при запуске
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{DISCOVERY_URL}/register", 
                             params={"name": SERVICE_NAME, "host": SERVICE_HOST, "port": SERVICE_PORT})
            print(f"[{SERVICE_NAME}] Сервис успешно зарегистрирован в Discovery")
        except Exception as e:
            print(f"[{SERVICE_NAME}] Ошибка регистрации: {e}")
    
    heartbeat_task = asyncio.create_task(send_heartbeat())
    yield
    heartbeat_task.cancel()

app = FastAPI(title="Reader Microservice (PZ4)", lifespan=lifespan)

# --- 5. ШАР CONTROLLER (API Endpoints) ---
@app.get("/readers", response_model=List[ReaderReadDTO])
def list_readers():
    """5. [Reader] Список всех читателей"""
    return [ReaderReadDTO(**r) for r in repo.get_all()]

@app.get("/readers/{id}", response_model=ReaderReadDTO)
def get_reader_by_id(id: int):
    """6. [Reader] Данные читателя по ID"""
    return ReaderBusinessService.get_reader(id)

@app.post("/readers", response_model=ReaderReadDTO)
def register_reader(dto: ReaderCreateDTO):
    """7. [Reader] Регистрация читателя"""
    return ReaderBusinessService.register(dto)

@app.put("/readers/{id}/status", response_model=ReaderReadDTO)
def update_status(id: int, status: str):
    """8. [Reader] Изменить статус читателя"""
    if status not in ["active", "blocked"]:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
    updated = repo.update_status_in_db(id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Читатель не найден")
    return ReaderReadDTO(**updated)

if __name__ == "__main__":
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)