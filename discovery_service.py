# discovery_service.py
from fastapi import FastAPI
import time
import uvicorn
from typing import Dict, List

app = FastAPI(title="Discovery Service (PZ4)")

# Сховище: { "service_name": [ {instance_info}, ... ] }
registry: Dict[str, List[dict]] = {}
TTL = 15  # Час життя сервісу без Heartbeat 

@app.post("/register")
def register(name: str, host: str, port: int):
    """Реєстрація сервісу в реєстрі [cite: 1047]"""
    if name not in registry:
        registry[name] = []
    
    # Видаляємо старі записи про цей же інстанс
    registry[name] = [s for s in registry[name] if not (s['host'] == host and s['port'] == port)]
    
    registry[name].append({
        "host": host,
        "port": port,
        "last_seen": time.time()
    })
    print(f"[Discovery] Зареєстровано: {name} ({host}:{port})")
    return {"status": "registered"}

@app.post("/heartbeat/{name}")
def heartbeat(name: str, host: str, port: int):
    """Оновлення статусу (Heartbeat) [cite: 1058]"""
    if name in registry:
        for instance in registry[name]:
            if instance['host'] == host and instance['port'] == port:
                instance['last_seen'] = time.time()
                return {"status": "alive"}
    return {"status": "not found"}

@app.get("/services/{name}")
def get_service_instances(name: str):
    """Отримання адрес за логічним іменем [cite: 1061, 1092]"""
    now = time.time()
    if name not in registry:
        return []
    
    # Фільтруємо тільки "живі" сервіси
    active = [s for s in registry[name] if now - s['last_seen'] < TTL]
    registry[name] = active
    return [{"host": s['host'], "port": s['port']} for s in active]

@app.get("/services")
def list_all():
    """Моніторинг реєстру [cite: 1063]"""
    return registry

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)