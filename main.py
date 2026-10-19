import logging
import sys
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError

import config
from handlers.message_handler import register_message_handlers
from handlers.event_handler import register_system_handlers

# 確保 Windows 終端機支援 UTF-8 (包含表情符號)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 設定 Log 格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("line_bot")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info("🚀 LINE Bot 伺服器啟動中...")
    if config.is_configured():
        logger.info("✅ LINE 憑證檢測通過 (Channel Secret & Access Token 已設定)")
    else:
        logger.warning("⚠️ 注意：尚未在 .env 中填寫真實的 LINE 憑證！")
        logger.warning("   請參閱 README.md 完成 LINE Developers 後台金鑰設定。")
    logger.info("==================================================")
    yield
    logger.info("🛑 LINE Bot 伺服器已停止。")

app = FastAPI(
    title="LINE Bot FastAPI Server",
    description="具備模組化事件處理與安全簽章驗證的 LINE Bot 伺服器",
    version="1.0.0",
    lifespan=lifespan
)

# 初始化 LINE WebhookHandler
handler = WebhookHandler(config.LINE_CHANNEL_SECRET if config.is_configured() else "default_dummy_secret")

# 註冊事件監聽器
register_message_handlers(handler)
register_system_handlers(handler)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "LINE Bot Webhook 伺服器運作正常",
        "line_configured": config.is_configured(),
        "webhook_endpoint": "/callback"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/callback")
@app.post("/webhook")
async def callback(request: Request, background_tasks: BackgroundTasks, x_line_signature: str = Header(None)):
    """
    接收 LINE Messaging API Webhook 事件的核心端點
    """
    if not x_line_signature:
        logger.warning("收到未附帶 X-Line-Signature 的 Callback 請求，已拒絕。")
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8")

    logger.info(f"收到 Webhook 請求 (長度: {len(body_text)} 位元組)")

    try:
        # 處理事件（FastAPI 非同步執行處理）
        handler.handle(body_text, x_line_signature)
    except InvalidSignatureError:
        logger.error("❌ 簽章驗證失敗 (Invalid signature)！請確認 LINE_CHANNEL_SECRET 是否正確。")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"❌ 處理 Webhook 事件時發生錯誤: {e}", exc_info=True)
        # 即使內部業務錯誤，LINE 要求一般需回傳 200 或 500，避免 LINE 持續重試發送
        return JSONResponse(status_code=200, content={"status": "handled_with_error", "detail": str(e)})

    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
