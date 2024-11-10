import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LLM_URL = os.getenv("LLM_URL", "http://llm:8000/")
    