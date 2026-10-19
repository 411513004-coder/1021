import logging
from linebot.v3.webhooks import (
    FollowEvent,
    UnfollowEvent,
    PostbackEvent
)
from services import line_service

logger = logging.getLogger("line_bot")

def register_system_handlers(handler):
    """註冊系統事件處理器（好友加入、封鎖、按鈕回傳等）"""

    @handler.add(FollowEvent)
    def handle_follow(event: FollowEvent):
        reply_token = event.reply_token
        user_id = event.source.user_id if event.source else "未知"
        logger.info(f"新用戶加入好友或解除封鎖: {user_id}")

        welcome_text = (
            "🎉 歡迎加入！我是您的智慧 LINE Bot 助理。\n\n"
            "您可以直接傳送任何訊息給我進行對話，或是輸入「說明」查看所有支援的指令。"
        )
        line_service.reply_text(
            reply_token,
            welcome_text,
            quick_reply_items=["說明", "ping", "關於"]
        )

    @handler.add(UnfollowEvent)
    def handle_unfollow(event: UnfollowEvent):
        user_id = event.source.user_id if event.source else "未知"
        logger.info(f"用戶已封鎖此機器人: {user_id}")

    @handler.add(PostbackEvent)
    def handle_postback(event: PostbackEvent):
        reply_token = event.reply_token
        postback_data = event.postback.data
        logger.info(f"收到按鈕互動回傳 (Postback): {postback_data}")

        line_service.reply_text(
            reply_token,
            f"📌 您點擊了按鈕互動，回傳資料為：{postback_data}",
            quick_reply_items=["說明", "ping"]
        )
