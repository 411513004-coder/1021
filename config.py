import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 讀取設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "").strip()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
PORT = int(os.getenv("PORT", "8000"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GAS_FAQ_URL = os.getenv("GAS_FAQ_URL", "").strip()

def is_configured() -> bool:
    """檢查 LINE 金鑰是否已完成設定"""
    placeholders = ["", "your_channel_secret_here", "your_channel_access_token_here"]
    if LINE_CHANNEL_SECRET in placeholders or LINE_CHANNEL_ACCESS_TOKEN in placeholders:
        return False
    return True

def is_gemini_configured() -> bool:
    """檢查 Google Gemini API Key 是否已設定"""
    placeholders = ["", "your_gemini_api_key_here"]
    if GEMINI_API_KEY in placeholders:
        return False
    return True

def is_faq_configured() -> bool:
    """檢查 Google 試算表 FAQ 網址是否已設定"""
    return bool(GAS_FAQ_URL and GAS_FAQ_URL.startswith("http"))


