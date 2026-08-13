import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID", "")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", TARGET_CHANNEL_ID)
DEFAULT_DONOR_URL = "https://t.me/s/vibecoding_tg"

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN sozlanmagan! .env faylni tekshiring.")

