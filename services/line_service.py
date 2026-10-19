import logging
import json
from typing import List, Union, Dict, Any

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    PostbackAction,
    URIAction
)
import config

logger = logging.getLogger("line_bot")

def get_messaging_api() -> MessagingApi:
    """獲取 MessagingApi 實例"""
    configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
    api_client = ApiClient(configuration)
    return MessagingApi(api_client)

def reply_text(reply_token: str, text: str, quick_reply_items: List[str] = None):
    """
    發送純文字訊息回覆（可附帶 Quick Reply 快捷按鈕）
    """
    if not config.is_configured():
        logger.warning("LINE 憑證尚未在 .env 中設定，略過傳送回覆訊息。")
        return

    quick_reply = None
    if quick_reply_items:
        items = [
            QuickReplyItem(action=MessageAction(label=item, text=item))
            for item in quick_reply_items
        ]
        quick_reply = QuickReply(items=items)

    messages = [TextMessage(text=text, quickReply=quick_reply)]
    req = ReplyMessageRequest(replyToken=reply_token, messages=messages)

    try:
        api = get_messaging_api()
        api.reply_message(req)
        logger.info(f"成功發送文字回覆至 token: {reply_token[:8]}...")
    except Exception as e:
        logger.error(f"發送文字回覆失敗: {e}", exc_info=True)

def reply_flex(reply_token: str, alt_text: str, flex_content: Dict[str, Any]):
    """
    發送結構化 Flex 訊息（彈性視覺卡片）
    """
    if not config.is_configured():
        logger.warning("LINE 憑證尚未在 .env 中設定，略過傳送 Flex 訊息。")
        return

    try:
        container = FlexContainer.from_json(json.dumps(flex_content))
        flex_msg = FlexMessage(altText=alt_text, contents=container)
        req = ReplyMessageRequest(replyToken=reply_token, messages=[flex_msg])
        api = get_messaging_api()
        api.reply_message(req)
        logger.info(f"成功發送 Flex 訊息至 token: {reply_token[:8]}...")
    except Exception as e:
        logger.error(f"發送 Flex 訊息失敗: {e}", exc_info=True)

def create_help_flex_bubble() -> Dict[str, Any]:
    """
    產生精美的繁體中文功能說明 Flex Bubble 卡片
    """
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#00B900",
            "paddingAll": "15px",
            "contents": [
                {
                    "type": "text",
                    "text": "🤖 LINE Bot 功能導覽",
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "size": "lg"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "歡迎使用！您可以嘗試發送以下指令：",
                    "color": "#555555",
                    "size": "sm",
                    "wrap": True
                },
                {"type": "separator"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🔹 ping",
                                    "weight": "bold",
                                    "size": "sm",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": "檢查伺服器連線與狀態",
                                    "size": "xs",
                                    "color": "#888888",
                                    "flex": 5
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🔹 說明 / help",
                                    "weight": "bold",
                                    "size": "sm",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": "顯示此功能卡片",
                                    "size": "xs",
                                    "color": "#888888",
                                    "flex": 5
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🔹 關於",
                                    "weight": "bold",
                                    "size": "sm",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": "查看機器人環境與版本資訊",
                                    "size": "xs",
                                    "color": "#888888",
                                    "flex": 5
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#00B900",
                    "height": "sm",
                    "action": {
                        "type": "message",
                        "label": "測試 Ping",
                        "text": "ping"
                    }
                },
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "LINE Developers 官方文件",
                        "uri": "https://developers.line.biz/zh-hant/docs/messaging-api/"
                    }
                }
            ]
        }
    }

def create_interactive_menu_carousel() -> Dict[str, Any]:
    """
    產生精美、可左右滑動的互動式圖文選單 (Flex Carousel)
    包含 AI 對話、工具箱與免費說明 3 大主題
    """
    return {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#4285F4",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🧠 免費 AI 智能對話",
                            "weight": "bold",
                            "color": "#FFFFFF",
                            "size": "md"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Google Gemini 2.5 Flash",
                            "weight": "bold",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": "隨時直接輸入任何問題，AI 助理會即時解答！支援前後對話上下文記憶。",
                            "size": "xs",
                            "color": "#666666",
                            "wrap": True
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#4285F4",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "請向我自我介紹",
                                "text": "請向我自我介紹，告訴我你能幫我做什麼？"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "🧹 清除對話記憶",
                                "text": "清除記憶"
                            }
                        }
                    ]
                }
            },
            {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#00B900",
                    "contents": [
                        {
                            "type": "text",
                            "text": "⚡ 常用工具箱",
                            "weight": "bold",
                            "color": "#FFFFFF",
                            "size": "md"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "系統檢測與資訊",
                            "weight": "bold",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": "快速檢查伺服器健康狀態、連線延遲或查看運行架構。",
                            "size": "xs",
                            "color": "#666666",
                            "wrap": True
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#00B900",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "🏓 測試 Ping",
                                "text": "ping"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "ℹ️ 關於機器人",
                                "text": "關於"
                            }
                        }
                    ]
                }
            },
            {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#F4B400",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🛡️ 100% 免費說明",
                            "weight": "bold",
                            "color": "#FFFFFF",
                            "size": "md"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "無須任何付費或信用卡",
                            "weight": "bold",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": "• LINE 被動回覆訊息：永久免費無上限\n• Google AI Studio：每日 1,500 次免費額度",
                            "size": "xs",
                            "color": "#666666",
                            "wrap": True
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#F4B400",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "免費領取 Key 教學",
                                "text": "領取key教學"
                            }
                        },
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "uri",
                                "label": "Google AI Studio 官網",
                                "uri": "https://aistudio.google.com/"
                            }
                        }
                    ]
                }
            }
        ]
    }

