import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("line_bot")

KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "ndhu_knowledge.json"

_kb_cache: Optional[Dict[str, Any]] = None

def _load_kb() -> Dict[str, Any]:
    global _kb_cache
    if _kb_cache is None:
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                _kb_cache = json.load(f)
            logger.info(f"知識庫載入成功：{KB_PATH}")
        except FileNotFoundError:
            logger.warning(f"知識庫檔案不存在：{KB_PATH}")
            _kb_cache = {}
        except json.JSONDecodeError as e:
            logger.error(f"知識庫 JSON 格式錯誤：{e}")
            _kb_cache = {}
    return _kb_cache

def reload_kb():
    global _kb_cache
    _kb_cache = None
    return _load_kb()

def search_knowledge(query: str, top_k: int = 5) -> List[str]:
    """從知識庫搜尋與 query 相關的知識條目"""
    kb = _load_kb()
    if not kb:
        return []

    query_lower = query.lower()
    results: List[Dict[str, Any]] = []

    stopwords = {"請問", "幫我", "告訴我", "什麼", "哪些", "有沒有",
                 "介紹", "說明", "是", "的", "在", "嗎", "呢"}
    keywords = [w for w in re.findall(r'[\u4e00-\u9fff\w]+', query)
                if w not in stopwords and len(w) >= 2]

    def score(text: str) -> int:
        s = 0
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                s += 2
        if query_lower in text_lower:
            s += 5
        return s

    # ── 大學基本資訊 ──
    uni = kb.get("university", {})
    uni_keywords = ["東華", "ndhu", "東華大學", "學校", "地址", "電話", "官網"]
    if any(kw in query_lower for kw in uni_keywords):
        note = uni.get("note", "")
        text = (
            f"【東華大學基本資訊】\n"
            f"正式名稱：{uni.get('name', '')}\n"
            f"英文名稱：{uni.get('english_name', '')}\n"
            f"地址：{uni.get('address', '')}\n"
            f"電話：{uni.get('phone', '')}\n"
            f"官網：{uni.get('website', '')}"
        )
        if note:
            text += f"\n重要說明：{note}"
        results.append({"score": 8, "text": text})

    # ── special_notes 特別查詢（如陳文盛教授） ──
    for key, note_data in kb.get("special_notes", {}).items():
        if any(kw in key for kw in keywords) or score(key) > 0:
            confirmed = note_data.get("confirmed_info", "")
            correct_dept = note_data.get("correct_department", "")
            wrong_info = note_data.get("wrong_info_to_correct", "")
            research = note_data.get("research_areas", "")
            text = (
                f"【特別說明：{key}】\n"
                f"正確資訊：{confirmed}\n"
            )
            if correct_dept:
                text += f"正確所屬：{correct_dept}\n"
            if research:
                text += f"研究領域：{research}\n"
            if wrong_info:
                text += f"⚠️ 常見錯誤：{wrong_info}\n"
            results.append({"score": 20, "text": text})

    # ── 各學院、系所、教授、課程 ──
    for college in kb.get("colleges", []):
        college_name = college.get("name", "")
        for dept in college.get("departments", []):
            dept_name = dept.get("name", "")
            dept_short = dept.get("short_name", "")
            dept_english = dept.get("english_name", "")
            dept_note = dept.get("note", "")

            dept_identifiers = [dept_name, dept_short, dept_english, college_name]
            dept_score = score(" ".join(dept_identifiers))
            if dept_score == 0:
                for kw in keywords:
                    if any(kw in d for d in dept_identifiers):
                        dept_score += 1

            # 教授搜尋
            for prof in dept.get("professors", []):
                prof_name = prof.get("name", "")
                prof_title = prof.get("title", "")
                prof_research = prof.get("research_areas", "")
                prof_email = prof.get("email", "")
                prof_lab = prof.get("lab", "")
                prof_note = prof.get("note", "")

                prof_text = f"{prof_name} {prof_title} {prof_research} {prof_lab} {prof_note}"
                prof_score = score(prof_text) + dept_score

                # ★ 姓名直接命中：無論系所分數高低都優先顯示
                name_hit = any(kw in prof_name for kw in keywords)
                if name_hit:
                    prof_score += 10

                if prof_score > 0 or name_hit:
                    fact = (
                        f"【教授資訊】\n"
                        f"姓名：{prof_name}\n"
                        f"職稱：{prof_title}\n"
                        f"所屬系所：{dept_name}（{college_name}）\n"
                    )
                    if prof_research:
                        fact += f"研究領域：{prof_research}\n"
                    if prof_lab:
                        fact += f"實驗室：{prof_lab}\n"
                    if prof_email:
                        fact += f"Email：{prof_email}\n"
                    if prof_note:
                        fact += f"備註：{prof_note}\n"
                    if dept_note:
                        fact += f"系所備註：{dept_note}\n"
                    results.append({"score": prof_score, "text": fact})

            # 課程搜尋
            course_keywords = ["課程", "開課", "必修", "選修", "科目", "學分", "規劃"]
            if any(kw in query_lower for kw in course_keywords) or dept_score > 0:
                courses = dept.get("courses", [])
                if courses:
                    course_list = "\n".join(
                        f"  • {c}" if isinstance(c, str)
                        else f"  • {c.get('name','')}（{c.get('credits','?')} 學分）"
                        for c in courses[:20]
                    )
                    results.append({
                        "score": dept_score + 2,
                        "text": (
                            f"【{dept_name} 課程規劃】\n"
                            f"所屬學院：{college_name}\n"
                            f"{course_list}"
                        )
                    })

            # 系所基本資訊
            if dept_score > 0:
                dept_info = f"【系所資訊】\n系所名稱：{dept_name}（{dept_short}）\n所屬學院：{college_name}\n"
                if dept_english:
                    dept_info += f"英文名稱：{dept_english}\n"
                if dept.get("website"):
                    dept_info += f"官網：{dept['website']}\n"
                if dept_note:
                    dept_info += f"備註：{dept_note}\n"
                results.append({"score": dept_score, "text": dept_info})

    # ── 餐廳搜尋 ──
    food_keywords = ["餐廳", "素食", "吃飯", "吃素", "蔬食", "餐", "美食",
                     "吉安", "壽豐", "附近", "館子", "用餐", "素食餐廳"]
    if any(kw in query_lower for kw in food_keywords):
        restaurants_data = kb.get("restaurants", {})

        for rest in restaurants_data.get("near_ndhu", []):
            rest_name = rest.get("name", "")
            rest_text = f"{rest_name} {rest.get('type','')} {rest.get('address','')} {rest.get('note','')}"
            rest_score = score(rest_text)

            fact = (
                f"【東華大學附近素食餐廳】\n"
                f"名稱：{rest_name}\n"
                f"地址：{rest.get('address', '未知')}\n"
                f"類型：{rest.get('type', '素食')}\n"
            )
            if rest.get("phone"):
                fact += f"電話：{rest['phone']}\n"
            if rest.get("hours"):
                fact += f"營業時間：{rest['hours']}\n"
            if rest.get("note"):
                fact += f"備註：{rest['note']}\n"
            results.append({"score": rest_score + 3, "text": fact})

        for rest in restaurants_data.get("jian_township", []):
            rest_name = rest.get("name", "")
            rest_text = f"{rest_name} {rest.get('type','')} {rest.get('address','')} {rest.get('note','')}"
            rest_score = score(rest_text)

            fact = (
                f"【吉安鄉素食餐廳】\n"
                f"名稱：{rest_name}\n"
                f"地址：{rest.get('address', '未知')}\n"
                f"類型：{rest.get('type', '素食')}\n"
            )
            if rest.get("phone"):
                fact += f"電話：{rest['phone']}\n"
            if rest.get("hours"):
                fact += f"營業時間：{rest['hours']}\n"
            if rest.get("note"):
                fact += f"備註：{rest['note']}\n"
            results.append({"score": rest_score + 3, "text": fact})

    # 排序、去重、取前 top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    seen = set()
    unique_results = []
    for r in results:
        if r["text"] not in seen and r["score"] > 0:
            seen.add(r["text"])
            unique_results.append(r["text"])
            if len(unique_results) >= top_k:
                break

    return unique_results


def get_knowledge_context(query: str) -> str:
    """回傳格式化的知識庫上下文字串，供注入 Gemini 系統提示詞使用"""
    facts = search_knowledge(query)
    if not facts:
        return ""

    context = "【以下是本地知識庫中的已驗證正確資訊，請以此為優先依據回答，不可與其矛盾】\n\n"
    context += "\n---\n".join(facts)
    return context
