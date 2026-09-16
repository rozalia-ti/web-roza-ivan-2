# Точка входа приложения: сборка FastAPI, обработка ошибок в едином формате,
# раздача фронтенда. Запускается командой: uvicorn app.main:app

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import router

app = FastAPI()
# Подключаем все маршруты из routes.py к приложению
app.include_router(router)


# Все HTTP-ошибки (404, 409 и т.д.) приводятся к единому формату {"error": "текст"}.
# Без этого FastAPI вернул бы {"detail": "текст"} — формат был бы разным для разных ошибок.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


# Ошибки валидации запроса (422): например, группа не подходит под шаблон.
# Из каждой ошибки берём только текст сообщения и склеиваем через "; ".
# Особый случай: если JSON в теле синтаксически битый, pydantic помечает ошибку
# типом json_* — по HTTP это 400 (плохой запрос), а не 422 (невалидные данные).
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = []

    for error in exc.errors():
        if error["type"].startswith("json_"):
            return JSONResponse(status_code=400, content={"error": "Некорректный JSON в теле запроса"})

        messages.append(error["msg"])

    return JSONResponse(status_code=422, content={"error": "; ".join(messages)})


# Ловушка на любой непредвиденный сбой: клиент получает JSON с 500,
# а не сырой traceback. Реальную причину видно в логах сервера.
@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Внутренняя ошибка сервера"})


# Раздача фронтенда из папки static: GET / отдаёт index.html.
# html=True включает отдачу index.html для корневого пути.
# Монтирование на "/" не перекрывает API: маршруты /api/...
# зарегистрированы раньше и проверяются первыми.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="static")
