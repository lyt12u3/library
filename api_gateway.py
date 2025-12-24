# api_gateway.py
import httpx
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import uvicorn
import random

# Конфигурация инфраструктуры 
DISCOVERY_URL = "http://127.0.0.1:8000"

async def get_service_url(service_name: str):
    """
    Динамическое обнаружение адреса сервиса.
    Реализует критерий 'Динамическая маршрутизация'.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{DISCOVERY_URL}/services/{service_name}")
            instances = resp.json()
            if not instances:
                raise HTTPException(status_code=503, detail=f"Сервис {service_name} не найден")
            
            # Балансировка нагрузки: выбираем случайный инстанс 
            instance = random.choice(instances)
            return f"http://{instance['host']}:{instance['port']}"
        except Exception:
            raise HTTPException(status_code=503, detail="Discovery Service недоступен")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Логика при запуске шлюза
    print("[Gateway] API Gateway запущен на порту 8080")
    yield
    # Логика при остановке
    print("[Gateway] API Gateway остановлен")

app = FastAPI(title="API Gateway (Fixed)", lifespan=lifespan)

@app.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request):
    """
    Универсальный прокси. 
    Принимает запросы вида: 8080/readers/list -> перенаправляет на актуальный порт Reader Service.
    """
    # 1. Получаем реальный адрес микросервиса по его имени 
    base_url = await get_service_url(service_name)
    
    # 2. Формируем чистый путь (убираем лишние слеши)
    clean_path = path.lstrip("/")
    # ВАЖНО: Большинство твоих микросервисов имеют префикс /catalog или /readers
    # Поэтому итоговый URL должен быть таким:
    url = f"{base_url}/{service_name}/{clean_path}"
    
    # 3. Подготовка данных
    body = await request.body()
    params = dict(request.query_params)
    
    # 4. Проксирование запроса с обработкой редиректов 
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            proxy_resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                params=params,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"}
            )
            
            # Пытаемся вернуть JSON, если нет — возвращаем текст ошибки
            try:
                return proxy_resp.json()
            except Exception:
                return {"detail": proxy_resp.text, "status_code": proxy_resp.status_code}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gateway Error: {str(e)}")

if __name__ == "__main__":
    # Единая точка входа для клиента 
    uvicorn.run(app, host="127.0.0.1", port=8080)