import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
    WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook/bot")
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    API_URL = os.getenv("API_URL")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8443))

