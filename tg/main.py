import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import asyncio

from aiogram import Dispatcher
from aiogram.types import Update

from app.tg.bot import bot, dp
from app.tg.config import Config
from app.tg.handlers import *  # Импорт всех обработчиков

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI()

# FastAPI маршрут для webhook
@app.post(Config.WEBHOOK_PATH)
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        asyncio.create_task(dp.process_update(update))
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return JSONResponse(status_code=400, content={"message": "Bad Request"})
    return JSONResponse(status_code=200, content={"message": "OK"})

# Настройка webhook при запуске приложения
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(Config.WEBHOOK_URL)
    logger.info(f"Webhook установлен на {Config.WEBHOOK_URL}")

# Удаление webhook при остановке приложения
@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logger.info("Webhook удален и хранилище закрыто")

# Точка входа
if __name__ == "__main__":
    uvicorn.run("app.main:app", host=Config.HOST, port=Config.PORT)
