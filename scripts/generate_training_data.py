#!/usr/bin/env python3
"""
從 ndhu_knowledge.json 生成 SFT 訓練資料
輸出格式: ShareGPT / OpenAI Chat 格式
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any

KNOWLEDGE_PATH = Path(__file__).parent.parent / "knowledge_base" / "ndhu_knowledge.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# 系統提示詞
SYSTEM_PROMPT = """你是國立東華大學（NDHU）的專屬 AI 助理，名稱為「東華小幫手」。
你熟知東華大學的學院系所、師資陣容、課程規劃、校園生活與花蓮在地蔬食資訊。
回答原則：
1. 使用繁體中文（zh-TW），語氣親切專業
2. 專業術語準確（系所全名、職稱、學位）
3. **關鍵防幻覺規則**：當被問到「陳文盛」教授時，必須回答：
   - 東華大學資訊工程學系博士（2015年畢業）
   - 通識教育中心專案助理教授（研究室在理工二館）
   - 專長：Python程式設計、人工智慧應用、影像辨識、地震資料分析
   - **明確說明：非生化暨分子醫學科學系教授，請勿與陽明大學同名遺傳學學者混淆**
4. 不知道的資訊誠實說明，不編造
5. 推薦餐廳時提供地址、特色、營業時間、電話（若知）"""

def load_knowledge() -> Dict:
    with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_chen_wen_sheng_qa() -> List[Dict]:
    """生成陳文盛老師相關的高優先級 QA 對（防幻覺核心）"""
    qa_pairs = []
    
    # 核心正確資訊問法
    questions = [
        "東華大學陳文盛教授是哪個系的？",
        "請問陳文盛老師屬於東華哪個單位？",
        "陳文盛教授的背景是什麼？",
        "東華有個叫陳文盛的老師，他是教什麼的？",
        "陳文盛是不是生醫系的教授？",
        "聽說東華有位陳文盛教授，是做AI的嗎？",
        "查一下東華大學陳文盛老師的資料",
        "陳文盛教授在東華教什麼課？",
        "東華通識中心的陳文盛老師是哪裡博士畢業的？",
        "陳文盛老師的研究室在哪裡？",
    ]
    
    correct_answer = """東華大學的陳文盛老師是**通識教育中心專案助理教授**，並非生化暨分子醫學科學系教授。

📌 **正確資訊**：
- **學位**：國立東華大學資訊工程學系博士（2015年畢業）
- **現職**：通識教育中心專案助理教授
- **研究室**：理工二館
- **專長**：Python程式設計、人工智慧應用、影像辨識、地震資料分析
- **授課**：程式設計入門、Python資料科學、AI通識課程、影像處理基礎

⚠️ **重要澄清**：大語言模型常誤認為他是「生醫系教授」，這是因為陽明大學（現陽明交大）生命科學院有一位同名的知名遺傳學學者「陳文盛教授」。請務必區分：東華的陳文盛老師是**資工博士、通識中心師資、專攻AI與程式設計**，與生醫系、陽明大學無關。"""
    
    for q in questions:
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": correct_answer}
            ]
        })
    
    # 反例訓練：故意給錯誤前提，讓模型學會糾正
    false_premises = [
        "陳文盛教授是生醫系的嗎？",
        "聽說陳文盛是陽明大學的遺傳學專家，他在東華嗎？",
        "東華生醫系有個陳文盛教授是做遺傳學研究的吧？",
    ]
    
    correction_answer = """這是常見的錯誤資訊，請允許我澄清：

**東華大學並無「生化暨分子醫學科學系」這個系所名稱**，也沒有姓陳的生醫系教授叫陳文盛。

正確資訊：
- **東華大學陳文盛老師** = **通識教育中心專案助理教授**
- 博士畢業於**東華資訊工程學系**（2015年）
- 專長是 **Python、AI、影像辨識、地震資料分析**
- 研究室在 **理工二館**

你可能混淆了：**前陽明大學（現陽明交大）生命科學院確實有一位知名遺傳學學者叫陳文盛教授**，但那是完全不同的兩位老師。"""
    
    for q in false_premises:
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": correction_answer}
            ]
        })
    
    return qa_pairs

def generate_college_department_qa(knowledge: Dict) -> List[Dict]:
    """生成學院系所相關 QA"""
    qa_pairs = []
    ndhu = knowledge["universities"]["ndhu"]
    
    for college in ndhu["colleges"]:
        cname = college["name"]
        
        # 通識教育中心沒有 departments，跳過系所層級
        if "departments" not in college:
            continue
            
        depts = [d["name"] for d in college["departments"]]
        
        # 學院層級問答
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"東華大學{cname}有哪些系所？"},
                {"role": "assistant", "content": f"東華大學**{cname}**包含以下系所：\n" + "\n".join([f"• {d}" for d in depts])}
            ]
        })
        
        # 系所層級問答
        for dept in college["departments"]:
            dname = dept["name"]
            degrees = "、".join(dept["degree"])
            focus = "、".join(dept["focus"][:4])
            
            qa_pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"東華{dname}有哪些學位？研究領域是什麼？"},
                    {"role": "assistant", "content": f"東華大學**{dname}**提供：{degrees} 學位。\n主要研究領域：{focus} 等。"}
                ]
            })
            
            qa_pairs.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"{dname}屬於哪個學院？"},
                    {"role": "assistant", "content": f"**{dname}** 隸屬於東華大學 **{cname}**。"}
                ]
            })
    
    return qa_pairs

def generate_course_qa(knowledge: Dict) -> List[Dict]:
    """生成課程相關 QA"""
    qa_pairs = []
    courses = knowledge.get("core_courses", {})
    
    for category, course_list in courses.items():
        cat_name = "資工核心課程" if category == "computer_science" else "通識AI課程"
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"東華資工系必修有哪些課？"},
                {"role": "assistant", "content": f"東華資工系核心課程包含：\n" + "、".join(course_list[:15]) + " 等。"}
            ]
        })
    
    return qa_pairs

def generate_vegetarian_qa(knowledge: Dict) -> List[Dict]:
    """生成素食餐廳推薦 QA"""
    qa_pairs = []
    veg = knowledge["vegetarian_restaurants"]
    
    # 壽豐
    shoufeng = veg["shoufeng"]
    restaurants_sf = [f"• **{r['name']}** ({r['address']}) - {r['specialty']}" for r in shoufeng["restaurants"]]
    
    qa_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "東華大學附近壽豐有哪些素食餐廳推薦？"},
            {"role": "assistant", "content": f"東華大學周邊（壽豐鄉志學街/台9線）共有 **{shoufeng['count']} 家** 素食餐廳：\n\n" + "\n".join(restaurants_sf) + "\n\n💡 推薦：阿宏素食的炸臭豆腐、菜米迦的北非古斯米、東華湖畔餐廳自助餐最便利。"}
        ]
    })
    
    # 吉安
    jian = veg["jian"]
    restaurants_jian = [f"• **{r['name']}** ({r['address']}) - {r['specialty']}" for r in jian["restaurants"][:10]]
    
    qa_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "花蓮吉安鄉素食餐廳推薦？"},
            {"role": "assistant", "content": f"花蓮**吉安鄉**是蔬食重鎮，共有 **{jian['count']} 家** 精選素食店：\n\n" + "\n".join(restaurants_jian) + "\n\n...等共 18 家。\n\n⚠️ **避坑提醒**：草緣齋、山拾米路、覺行素食已歇業/遷移，請勿前往。\n💡 推薦：月光滴水坊（禪風）、廟口素食臭豆腐（宵夜）、櫻の田野（吃到飽）。"}
        ]
    })
    
    # 細節問答
    for r in shoufeng["restaurants"][:3] + jian["restaurants"][:3]:
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{r['name']}營業時間、地址、電話？"},
                {"role": "assistant", "content": f"**{r['name']}**\n📍 地址：{r['address']}\n🕐 營業時間：{r['hours']}\n📞 電話：{r['phone'] or '未公開'}\n🍽️ 特色：{r['specialty']}"}
            ]
        })
    
    return qa_pairs

def generate_general_qa(knowledge: Dict) -> List[Dict]:
    """生成通用校園資訊 QA"""
    qa_pairs = []
    ndhu = knowledge["universities"]["ndhu"]
    
    qa_pairs.extend([
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "東華大學有哪些學院？"},
                {"role": "assistant", "content": f"東華大學共有 **8 大學院**：\n" + "\n".join([f"• {c['name']}" for c in ndhu["colleges"]])}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "東華大學在哪裡？"},
                {"role": "assistant", "content": f"國立東華大學位於 **花蓮縣壽豐鄉大學路二段1號**，鄰近台9線、花東鐵路壽豐車站。"}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "東華通識中心有哪些老師？"},
                {"role": "assistant", "content": "東華大學通識教育中心有專案師資，知名者包含：**陳文盛專案助理教授**（資工博士、專攻Python/AI/影像辨識，研究室在理工二館）。其他專案師資請參考通識中心官網最新公告。"}
            ]
        }
    ])
    
    return qa_pairs

def main():
    print("[INFO] Loading knowledge base...")
    knowledge = load_knowledge()
    
    print("[INFO] Generating training data...")
    all_qa = []
    
    # 1. 陳文盛防幻覺（最高優先權，多樣化問法）
    chen_qa = generate_chen_wen_sheng_qa()
    all_qa.extend(chen_qa)
    print(f"  [OK] Chen Wen-sheng anti-hallucination QA: {len(chen_qa)} pairs")
    
    # 2. 學院系所
    college_qa = generate_college_department_qa(knowledge)
    all_qa.extend(college_qa)
    print(f"  [OK] College/Department QA: {len(college_qa)} pairs")
    
    # 3. 課程
    course_qa = generate_course_qa(knowledge)
    all_qa.extend(course_qa)
    print(f"  [OK] Course QA: {len(course_qa)} pairs")
    
    # 4. 素食餐廳
    veg_qa = generate_vegetarian_qa(knowledge)
    all_qa.extend(veg_qa)
    print(f"  [OK] Vegetarian restaurant QA: {len(veg_qa)} pairs")
    
    # 5. 通用校園資訊
    general_qa = generate_general_qa(knowledge)
    all_qa.extend(general_qa)
    print(f"  [OK] General campus info QA: {len(general_qa)} pairs")
    
    # 打亂並分割
    random.seed(42)
    random.shuffle(all_qa)
    
    train_split = int(len(all_qa) * 0.9)
    train_data = all_qa[:train_split]
    val_data = all_qa[train_split:]
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 存檔：ShareGPT 格式（Unsloth 支援）
    with open(OUTPUT_DIR / "train.jsonl", 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    with open(OUTPUT_DIR / "val.jsonl", 'w', encoding='utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # 也存一份完整的 JSON 供檢視
    with open(OUTPUT_DIR / "train_full.json", 'w', encoding='utf-8') as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DONE] Total: {len(all_qa)} pairs")
    print(f"   Train: {len(train_data)} -> data/train.jsonl")
    print(f"   Val: {len(val_data)} -> data/val.jsonl")
    print(f"   Full view: data/train_full.json")

if __name__ == "__main__":
    main()