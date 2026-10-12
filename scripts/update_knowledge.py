#!/usr/bin/env python3
"""
知識庫更新腳本
提供 CLI 介面快速追加教授、課程或餐廳資料
並自動重新生成訓練資料
"""
import json
import argparse
from pathlib import Path
from typing import Dict, Any

KNOWLEDGE_PATH = Path(__file__).parent.parent / "knowledge_base" / "ndhu_knowledge.json"

def load_knowledge() -> Dict:
    with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_knowledge(knowledge: Dict):
    with open(KNOWLEDGE_PATH, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    print(f"[OK] 知識庫已更新: {KNOWLEDGE_PATH}")

def add_professor(knowledge: Dict, name: str, title: str, college: str, 
                  department: str, phd: str, specialties: list, courses: list, 
                  office: str = "", correction: str = ""):
    """新增/更新教授資訊"""
    # 找到對應學院
    for c in knowledge["universities"]["ndhu"]["colleges"]:
        if c["name"] == college:
            if "faculty" not in c:
                c["faculty"] = []
            
            # 檢查是否已存在
            for i, f in enumerate(c["faculty"]):
                if f["name"] == name:
                    c["faculty"][i] = {
                        "name": name,
                        "title": title,
                        "phd": phd,
                        "office": office,
                        "specialties": specialties,
                        "courses": courses,
                        "correction": correction,
                        "verification": "手動更新"
                    }
                    print(f"[OK] 更新現有教授: {name}")
                    return
            
            # 新增
            c["faculty"].append({
                "name": name,
                "title": title,
                "phd": phd,
                "office": office,
                "specialties": specialties,
                "courses": courses,
                "correction": correction,
                "verification": "手動新增"
            })
            print(f"[OK] 新增教授: {name} 到 {college}")
            return
    
    print(f"[ERROR] 找不到學院: {college}")

def add_restaurant(knowledge: Dict, area: str, name: str, address: str,
                   specialty: str, rtype: str, hours: str, phone: str = "",
                   note: str = ""):
    """新增素食餐廳"""
    if area not in knowledge["vegetarian_restaurants"]:
        print(f"[ERROR] 區域錯誤，可用: {list(knowledge['vegetarian_restaurants'].keys())}")
        return
    
    restaurants = knowledge["vegetarian_restaurants"][area]["restaurants"]
    
    # 檢查是否已存在
    for i, r in enumerate(restaurants):
        if r["name"] == name:
            restaurants[i] = {
                "name": name,
                "address": address,
                "specialty": specialty,
                "type": rtype,
                "hours": hours,
                "phone": phone,
                "note": note
            }
            print(f"[OK] 更新餐廳: {name}")
            return
    
    restaurants.append({
        "name": name,
        "address": address,
        "specialty": specialty,
        "type": rtype,
        "hours": hours,
        "phone": phone,
        "note": note
    })
    knowledge["vegetarian_restaurants"][area]["count"] = len(restaurants)
    print(f"[OK] 新增餐廳: {name} 到 {area}")

def add_closed_restaurant(knowledge: Dict, area: str, name: str):
    """標記歇業餐廳"""
    if area not in knowledge["vegetarian_restaurants"]:
        return
    
    closed = knowledge["vegetarian_restaurants"][area].get("closed_restaurants", [])
    if name not in closed:
        closed.append(name)
        knowledge["vegetarian_restaurants"][area]["closed_restaurants"] = closed
        print(f"[OK] 標記歇業: {name}")

def list_colleges(knowledge: Dict):
    """列出所有學院"""
    for c in knowledge["universities"]["ndhu"]["colleges"]:
        dept_count = len(c.get("departments", []))
        faculty_count = len(c.get("faculty", []))
        print(f"  {c['name']}: {dept_count} 系所, {faculty_count} 專案師資")

def list_restaurants(knowledge: Dict, area: str = None):
    """列出餐廳"""
    areas = [area] if area else knowledge["vegetarian_restaurants"].keys()
    for a in areas:
        data = knowledge["vegetarian_restaurants"][a]
        print(f"\n{a} ({data['count']} 家):")
        for r in data["restaurants"]:
            print(f"  • {r['name']} - {r['specialty']} ({r['hours']})")
        if data.get("closed_restaurants"):
            print(f"  ⚠️ 歇業: {', '.join(data['closed_restaurants'])}")

def main():
    parser = argparse.ArgumentParser(description="NDHU 知識庫管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 新增教授
    p_prof = subparsers.add_parser("add-prof", help="新增/更新教授")
    p_prof.add_argument("--name", required=True, help="姓名")
    p_prof.add_argument("--title", required=True, help="職稱 (如: 專案助理教授)")
    p_prof.add_argument("--college", required=True, help="學院 (如: 通識教育中心)")
    p_prof.add_argument("--phd", required=True, help="博士學位 (如: 東華資工系 2015)")
    p_prof.add_argument("--specialties", nargs="+", required=True, help="專長列表")
    p_prof.add_argument("--courses", nargs="+", required=True, help="授課列表")
    p_prof.add_argument("--office", default="", help="研究室位置")
    p_prof.add_argument("--correction", default="", help="防幻覺註記")
    
    # 新增餐廳
    p_rest = subparsers.add_parser("add-restaurant", help="新增/更新素食餐廳")
    p_rest.add_argument("--area", required=True, choices=["shoufeng", "jian"], help="區域")
    p_rest.add_argument("--name", required=True, help="餐廳名稱")
    p_rest.add_argument("--address", required=True, help="地址")
    p_rest.add_argument("--specialty", required=True, help="招牌菜/特色")
    p_rest.add_argument("--type", required=True, help="類型 (如: 老字號、吃到飽、宵夜)")
    p_rest.add_argument("--hours", required=True, help="營業時間")
    p_rest.add_argument("--phone", default="", help="電話")
    p_rest.add_argument("--note", default="", help="備註")
    
    # 標記歇業
    p_closed = subparsers.add_parser("mark-closed", help="標記歇業餐廳")
    p_closed.add_argument("--area", required=True, choices=["shoufeng", "jian"])
    p_closed.add_argument("--name", required=True, help="餐廳名稱")
    
    # 列出
    p_list = subparsers.add_parser("list", help="列出資料")
    p_list.add_argument("--colleges", action="store_true", help="列出學院")
    p_list.add_argument("--restaurants", nargs="?", const="all", help="列出餐廳 (可指定區域)")
    
    # 重新生成訓練資料
    subparsers.add_parser("regen-data", help="重新生成訓練資料")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    knowledge = load_knowledge()
    
    if args.command == "add-prof":
        add_professor(knowledge, args.name, args.title, args.college, 
                     "", args.phd, args.specialties, args.courses, 
                     args.office, args.correction)
        save_knowledge(knowledge)
        
    elif args.command == "add-restaurant":
        add_restaurant(knowledge, args.area, args.name, args.address,
                      args.specialty, args.type, args.hours, args.phone, args.note)
        save_knowledge(knowledge)
        
    elif args.command == "mark-closed":
        add_closed_restaurant(knowledge, args.area, args.name)
        save_knowledge(knowledge)
        
    elif args.command == "list":
        if args.colleges:
            list_colleges(knowledge)
        if args.restaurants:
            list_restaurants(knowledge, None if args.restaurants == "all" else args.restaurants)
            
    elif args.command == "regen-data":
        print("[INFO] 重新生成訓練資料...")
        import subprocess
        result = subprocess.run(["python", "scripts/generate_training_data.py"], 
                              capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

if __name__ == "__main__":
    main()