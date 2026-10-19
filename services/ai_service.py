import logging
from typing import Dict, List, Optional
import config
from services.knowledge_service import get_knowledge_context

logger = logging.getLogger("line_bot")

# 記憶體對話暫存：user_id -> [{"role": "user"|"model", "text": "..."}]
# 保留最近 8 則訊息以提供多輪對話上下文
_CONVERSATION_HISTORY: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY_PER_USER = 8

def clear_user_history(user_id: str) -> bool:
    """清除指定使用者的對話記憶"""
    if user_id in _CONVERSATION_HISTORY:
        del _CONVERSATION_HISTORY[user_id]
        return True
    return False

def get_gemini_free_guide() -> str:
    """提供免費取得 Google Gemini API Key 的指引文字"""
    return (
        "💡【尚未啟用免費 AI 智慧對話】\n\n"
        "Google Gemini 提供每分鐘 15 次、每天 1,500 次的【完全免費】額度（免綁信用卡）！\n\n"
        "👉 領取步驟（約 1 分鐘）：\n"
        "1. 前往 Google AI Studio：https://aistudio.google.com/\n"
        "2. 登入 Google 帳號並點擊「Get API key」\n"
        "3. 點擊「Create API key」複製金鑰\n"
        "4. 貼入專案的 .env 檔案中的 GEMINI_API_KEY=\n\n"
        "設定好後，只要在 LINE 輸入任何問題，AI 就會直接親切回覆您！"
    )

def ask_gemini(user_id: str, prompt: str) -> str:
    """
    呼叫 Google Gemini 免費模型生成繁體中文回覆。
    整合本地 RAG 知識庫：自動搜尋東華大學相關事實，
    注入系統提示詞以修正 AI 幻覺，確保回答以正確資料為準。
    支援多輪對話記憶與異常防護。
    """
    if not config.is_gemini_configured():
        return get_gemini_free_guide()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)

        # 取得使用者先前的歷史紀錄
        history = _CONVERSATION_HISTORY.setdefault(user_id, [])

        # 建構包含歷史上下文的對話內容
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["text"])]
                )
            )

        # 加入當前最新問題
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        )

        # ── RAG 知識庫搜尋 ──
        # 根據使用者問題，自動從本地知識庫取出相關事實
        knowledge_context = get_knowledge_context(prompt)
        if knowledge_context:
            logger.info(f"知識庫命中！為使用者 {user_id} 注入 {len(knowledge_context)} 字元的背景知識")

        base_instruction = (
            "你是運行在 LINE 上的專業智慧助理，名叫「我的 AI 助理」，"
            "同時也是國立東華大學（NDHU）的校園助理，熟悉校園資訊。"
            "請一律使用台灣繁體中文（zh-TW）回答，語氣友善、專業、條理清晰。"
            "回答請針對手機通訊軟體的閱讀體驗排版，善用條列與適量表情符號，避免冗長空洞的套話。"
            "如果被問及技術、生活、摘要或規劃問題，請給出實用且準確的建議。"
        )

        # 若有知識庫命中，強制附加到系統指令最前端
        if knowledge_context:
            system_instruction = (
                knowledge_context + "\n\n"
                "【重要指示】以上知識庫內容為已驗證的正確資料，"
                "若知識庫資料與你的訓練資料有衝突，"
                "請絕對以知識庫資料為準，不可忽略或矛盾。\n\n"
                + base_instruction
            )
        else:
            system_instruction = base_instruction

        # 呼叫 Gemini 免費模型 (優先 gemini-3.5-flash-lite，若繁忙切換 gemini-3.8-flash)
        model_name = "gemini-3.5-flash-lite"
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=1200,
                )
            )
        except Exception as model_err:
            logger.warning(f"{model_name} 呼叫異常 ({model_err})，嘗試切換備用模型 gemini-3.8-flash")
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=1200,
                )
            )

        reply_text = response.text.strip() if response.text else "抱歉，目前暫時無法產生回應，請稍後再試。"

        # 更新歷史紀錄
        history.append({"role": "user", "text": prompt})
        history.append({"role": "model", "text": reply_text})

        # 超過上限時修剪最舊的紀錄
        if len(history) > MAX_HISTORY_PER_USER:
            _CONVERSATION_HISTORY[user_id] = history[-MAX_HISTORY_PER_USER:]

        return reply_text

    except Exception as e:
        logger.error(f"Gemini API 呼叫失敗: {e}", exc_info=True)
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "400" in err_msg:
            return "⚠️ Gemini API Key 似乎無效，請檢查 .env 中的 GEMINI_API_KEY 是否正確。"
        elif "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            return "⏳ 目前免費額度請求頻率稍微超出限制，請稍候 30 秒再試一次！"
        else:
            return f"抱歉，AI 處理訊息時發生了一點狀況：{err_msg[:60]}... 請稍後再試。"
