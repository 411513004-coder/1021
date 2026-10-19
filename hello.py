def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """計算 BMI 數值（身高公分、體重公斤）"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def get_bmi_category(bmi: float) -> str:
    """依據衛福部標準判斷體位區間"""
    if bmi < 18.5:
        return "體重過輕"
    elif bmi < 24:
        return "健康體位 (正常)"
    elif bmi < 27:
        return "過重"
    elif bmi < 30:
        return "輕度肥胖"
    elif bmi < 35:
        return "中度肥胖"
    else:
        return "重度肥胖"


def calculate_ideal_weight_range(height_cm: float) -> tuple[float, float]:
    """計算正常 BMI (18.5 ~ 24) 下的建議健康體重範圍 (kg)"""
    height_m = height_cm / 100
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.0 * (height_m ** 2)
    return min_weight, max_weight


def main():
    print("========================================")
    print("       Hello, World! 歡迎使用 BMI 系統    ")
    print("========================================\n")
    
    try:
        height_input = input("請輸入身高 (cm): ").strip()
        weight_input = input("請輸入體重 (kg): ").strip()

        height = float(height_input)
        weight = float(weight_input)

        if height <= 0 or weight <= 0:
            print("\n[錯誤] 身高與體重必須大於 0！")
            return

        bmi = calculate_bmi(height, weight)
        category = get_bmi_category(bmi)
        min_w, max_w = calculate_ideal_weight_range(height)

        print("\n----------- 計算結果 -----------")
        print(f"您的身高: {height:.1f} cm")
        print(f"您的體重: {weight:.1f} kg")
        print(f"BMI 指數: {bmi:.2f}")
        print(f"體位判定: {category}")
        print(f"建議健康體重範圍: {min_w:.1f} kg ~ {max_w:.1f} kg")
        print("--------------------------------")
    except ValueError:
        print("\n[錯誤] 請輸入有效的數值（整數或浮點數）。")


if __name__ == "__main__":
    main()

