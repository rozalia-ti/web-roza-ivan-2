# Точка входа: сборка FastAPI, единый формат ошибок, раздача статики.
# Python и JS общаются только по HTTP с JSON: JS (fetch) → routes → services → storage,
# обратно: dict → JSON → JS (response.json()). Запуск: uvicorn app.main:app

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import router

app = FastAPI()
# Подключаем маршруты из routes.py
app.include_router(router)


# Все HTTP-ошибки (404, 409...) в едином виде {"error": "..."}.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


# Ошибки валидации (422): тексты склеиваются через "; ".
# Битый JSON в теле — это 400 (плохой запрос), а не 422.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = []

    for error in exc.errors():
        if error["type"].startswith("json_"):
            return JSONResponse(status_code=400, content={"error": "Некорректный JSON в теле запроса"})

        messages.append(error["msg"])

    return JSONResponse(status_code=422, content={"error": "; ".join(messages)})


# Любой непредвиденный сбой — JSON с 500 вместо сырого traceback.
@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Внутренняя ошибка сервера"})


# Раздача фронтенда из static: Python отдаёт index.html/js/css как файлы, не исполняя их.
# Маршруты /api/... зарегистрированы раньше и не перекрываются монтированием "/".
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="static")
