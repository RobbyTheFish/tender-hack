from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import report

app = FastAPI(
    title="FastAPI Application",
    description="API для генерации отчетов и взаимодействия с Telegram ботом.",
    version="1.0.0"
)

# Подключение CORS middleware, если необходимо
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ограничьте по необходимости
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Включение маршрутов из модулей
app.include_router(report.router, prefix="/api", tags=["Report"])