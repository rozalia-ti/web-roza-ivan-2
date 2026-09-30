from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import router

app = FastAPI()
app.include_router(router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code, 
        content={"error": str(exc.detail)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = []

    for error in exc.errors():
        if error["type"].startswith("json_"):
            return JSONResponse(
                status_code=400, 
                content={"error": "Некорректный JSON в теле запроса"}
            )

        messages.append(error["msg"])

    return JSONResponse(
        status_code=422, 
        content={"error": "; ".join(messages)}
    )


@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, 
        content={"error": "Внутренняя ошибка сервера"}
    )


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static", html=True), name="static")
