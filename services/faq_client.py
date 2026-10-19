import os
import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

import config

logger = logging.getLogger("line_bot")

def get_gas_faq_url() -> str:
    """取得當前設定的 GAS FAQ URL"""
    return config.GAS_FAQ_URL or os.environ.get("GAS_FAQ_URL", "").strip()

def search_faq(question: str, timeout: float = 3.5) -> Dict[str, Any]:
    """
    向 Google Apps Script (GAS) 知識資料庫發送查詢請求
    
    回傳格式範例:
    - 命中: {"found": True, "answer": "每週一上午 09:10 上課", "matched_question": "請問幾點上課？"}
    - 未命中: {"found": False, "message": "知識庫中無適當答案"}
    - 異常/未設定: {"found": False, "error": "說明"}
    """
    gas_url = get_gas_faq_url()
    if not gas_url:
        # 尚未設定 GAS URL 時，視為未命中，讓主程式直接 fallback 給 AI
        return {"found": False, "message": "GAS_FAQ_URL 尚未設定"}

    clean_q = question.strip()
    if not clean_q:
        return {"found": False, "message": "問題為空"}

    try:
        # 透過 GET 帶上 ?q=... 查詢
        params = urllib.parse.urlencode({"q": clean_q})
        url = f"{gas_url}?{params}"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LINE-Bot-Python-Client/1.0"}
        )
        
        logger.info(f"正在向 Google 試算表 FAQ 查詢: '{clean_q}'")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            raw_data = response.read().decode("utf-8")
            
            if status_code == 200:
                data = json.loads(raw_data)
                if data.get("found"):
                    logger.info(f"✅ Google 試算表 FAQ 命中！題目: {data.get('matched_question')}")
                else:
                    logger.info("ℹ️ Google 試算表 FAQ 未命中，將轉由 AI 備援回答。")
                return data
            else:
                logger.warning(f"GAS FAQ API 回應非 200 代碼: {status_code}")
                return {"found": False, "error": f"HTTP {status_code}"}

    except Exception as e:
        # 網路逾時或 GAS 異常時，優雅降級，記錄 warning 後不中斷程式
        logger.warning(f"⚠️ 查詢 GAS FAQ 時發生異常 (將自動切換為 AI 備援): {e}")
        return {"found": False, "error": str(e)}
