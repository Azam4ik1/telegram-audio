import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
DB_PATH = os.environ.get("DB_PATH", "expenses.db")
TZ = "Asia/Dushanbe"
ZONE = ZoneInfo(TZ)
