#!/usr/bin/env python3
"""
知識庫管理工具
用法：
  python scripts/update_knowledge.py --add-professor   # 新增教授
  python scripts/update_knowledge.py --add-course      # 新增課程  
  python scripts/update_knowledge.py --add-restaurant  # 新增餐廳
  python scripts/update_knowledge.py --list            # 列出所有系所
  python scripts/update_knowledge.py --test "問題字串"  # 測試搜尋
"""
import json
import sys
import argparse
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "ndhu_knowledge.json"

def load_kb():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_kb(kb):
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print("✅ 知識庫已儲存！")

def list_departments(kb):
    print("\n📚 東華大學各學院系所清單：")
    for college in kb.get("colleges", []):
        print(f"\n🏛️  {college['name']}")
        for dept in college.get("departments", []):
            prof_count = len(dept.get("professors", []))
            course_count = len(dept.get("courses", []))
            print(f"   ├─ {dept['name']}（{dept.get('short_name','')}）"
                  f" | 教授：{prof_count} 位 | 課程：{course_count} 門")

def add_professor(kb):
    print("\n📝 新增教授資訊")
    print("─" * 40)

    # 列出系所供選擇
    dept_list = []
    for college in kb.get("colleges", []):
        for dept in college.get("departments", []):
            dept_list.append((college["name"], dept))

    print("請選擇系所：")
    for i, (college_name, dept) in enumerate(dept_list, 1):
        print(f"  {i:2d}. {dept['name']}（{college_name}）")

    try:
        choice = int(input("\n輸入編號：")) - 1
        _, selected_dept = dept_list[choice]
    except (ValueError, IndexError):
        print("❌ 無效選擇")
        return

    prof = {
        "name": input("教授姓名（例：陳文盛）：").strip(),
        "title": input("職稱（教授/副教授/助理教授）：").strip() or "教授",
        "research_areas": input("研究領域（用、分隔）：").strip(),
        "email": input("Email（可空白）：").strip(),
        "lab": input("實驗室名稱（可空白）：").strip(),
    }

    if not prof["name"]:
        print("❌ 姓名不可空白")
        return

    selected_dept.setdefault("professors", []).append(prof)
    save_kb(kb)
    print(f"✅ 已新增教授：{prof['name']} → {selected_dept['name']}")

def add_restaurant(kb):
    print("\n🍽️  新增素食餐廳資訊")
    print("─" * 40)
    area = input("地區（1=東華附近/壽豐，2=吉安鄉）：").strip()
    key = "near_ndhu" if area == "1" else "jian_township"

    rest = {
        "name": input("餐廳名稱：").strip(),
        "address": input("地址：").strip(),
        "phone": input("電話（可空白）：").strip(),
        "hours": input("營業時間（可空白）：").strip(),
        "type": input("類型（純素食/蔬食/葷素皆有）：").strip() or "素食",
        "note": input("備註（可空白）：").strip(),
    }

    if not rest["name"]:
        print("❌ 餐廳名稱不可空白")
        return

    kb.setdefault("restaurants", {}).setdefault(key, []).append(rest)
    save_kb(kb)
    print(f"✅ 已新增餐廳：{rest['name']}")

def test_search(query: str):
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from services.knowledge_service import search_knowledge, get_knowledge_context
    print(f"\n🔍 測試搜尋：「{query}」")
    print("─" * 40)
    results = search_knowledge(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"\n[結果 {i}]\n{r}")
    else:
        print("⚠️  知識庫中找不到相關資訊（將由 Gemini 直接回答）")

    context = get_knowledge_context(query)
    print(f"\n📊 注入提示詞長度：{len(context)} 字元")

def main():
    parser = argparse.ArgumentParser(description="東華大學知識庫管理工具")
    parser.add_argument("--list", action="store_true", help="列出所有系所")
    parser.add_argument("--add-professor", action="store_true", help="新增教授")
    parser.add_argument("--add-restaurant", action="store_true", help="新增餐廳")
    parser.add_argument("--test", type=str, metavar="問題", help="測試知識庫搜尋")
    args = parser.parse_args()

    if args.test:
        test_search(args.test)
        return

    kb = load_kb()

    if args.list:
        list_departments(kb)
    elif args.add_professor:
        add_professor(kb)
    elif args.add_restaurant:
        add_restaurant(kb)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
