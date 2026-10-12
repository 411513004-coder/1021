#!/usr/bin/env python3
"""
測試微調後的模型
支援載入 LoRA adapters 或合併後的模型
"""
import argparse
import torch
from unsloth import FastLanguageModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def load_model(model_path, base_model="unsloth/Qwen2.5-7B-Instruct-bnb-4bit", 
               max_seq_length=2048, load_in_4bit=True):
    """載入微調後的模型"""
    print(f"[INFO] Loading base model: {base_model}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )
    
    print(f"[INFO] Loading LoRA adapters from: {model_path}")
    model = PeftModel.from_pretrained(model, model_path)
    
    # 合併 LoRA 到基礎模型 (推理更快)
    print("[INFO] Merging LoRA adapters...")
    model = model.merge_and_unload()
    
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def load_merged_model(model_path, max_seq_length=2048):
    """直接載入已合併的模型"""
    print(f"[INFO] Loading merged model from: {model_path}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=False,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def chat(model, tokenizer, messages, max_new_tokens=512, temperature=0.7, top_p=0.9):
    """單輪對話"""
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # 只取生成的部分
    response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    return response

def interactive_chat(model, tokenizer):
    """互動式對話模式"""
    print("\n" + "="*60)
    print("NDHU Qwen 2.5 7B - 互動測試模式")
    print("輸入 'exit' 或 'quit' 結束")
    print("輸入 'clear' 清除對話歷史")
    print("="*60 + "\n")
    
    messages = [
        {"role": "system", "content": """你是國立東華大學（NDHU）的專屬 AI 助理，名稱為「東華小幫手」。
你熟知東華大學的學院系所、師資陣容、課程規劃、校園生活與花蓮在地蔬食資訊。
回答原則：
1. 使用繁體中文（zh-TW），語氣親切專業
2. 專業術語準確（系所全名、職稱、學位）
3. 關鍵防幻覺規則：當被問到「陳文盛」教授時，必須回答：
   - 東華大學資訊工程學系博士（2015年畢業）
   - 通識教育中心專案助理教授（研究室在理工二館）
   - 專長：Python程式設計、人工智慧應用、影像辨識、地震資料分析
   - 明確說明：非生化暨分子醫學科學系教授，請勿與陽明大學同名遺傳學學者混淆
4. 不知道的資訊誠實說明，不編造"""}
    ]
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 再見！")
                break
            if user_input.lower() in ['clear', 'c']:
                messages = [messages[0]]  # 保留 system
                print("[系統] 對話歷史已清除")
                continue
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            print("\n🤖 東華小幫手: ", end="", flush=True)
            response = chat(model, tokenizer, messages)
            print(response)
            
            messages.append({"role": "assistant", "content": response})
            
            # 限制歷史長度
            if len(messages) > 10:
                messages = [messages[0]] + messages[-8:]
                
        except KeyboardInterrupt:
            print("\n\n👋 再見！")
            break
        except Exception as e:
            print(f"\n[錯誤] {e}")

def run_test_cases(model, tokenizer):
    """執行預設測試案例"""
    test_cases = [
        "東華大學陳文盛教授是哪個系的？",
        "陳文盛老師是不是生醫系的教授？",
        "聽說陳文盛是陽明大學的遺傳學專家，他在東華嗎？",
        "東華大學有哪些學院？",
        "東華資工系有哪些核心課程？",
        "東華大學附近壽豐有哪些素食餐廳推薦？",
        "花蓮吉安鄉素食餐廳推薦？",
        "東華通識中心的陳文盛老師是哪裡博士畢業的？",
        "陳文盛老師教什麼課？",
        "東華大學在哪裡？",
    ]
    
    print("\n" + "="*60)
    print("自動測試案例")
    print("="*60)
    
    system_msg = {"role": "system", "content": """你是國立東華大學（NDHU）的專屬 AI 助理，名稱為「東華小幫手」。
回答原則：繁體中文、專業術語準確、陳文盛老師必須正確回答（通識中心專案助理教授、資工博士、非生醫系）。"""}
    
    for i, question in enumerate(test_cases, 1):
        messages = [system_msg, {"role": "user", "content": question}]
        print(f"\n[測試 {i}/{len(test_cases)}] Q: {question}")
        response = chat(model, tokenizer, messages, temperature=0.3)
        print(f"A: {response}")
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Test fine-tuned NDHU model")
    parser.add_argument("--model_path", type=str, required=True,
                        help="Path to LoRA adapters or merged model")
    parser.add_argument("--base_model", type=str, 
                        default="unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
                        help="Base model name (for LoRA loading)")
    parser.add_argument("--merged", action="store_true",
                        help="Load as merged model (not LoRA)")
    parser.add_argument("--max_seq_length", type=int, default=2048)
    parser.add_argument("--interactive", action="store_true",
                        help="Run interactive chat mode")
    parser.add_argument("--test_cases", action="store_true",
                        help="Run predefined test cases")
    args = parser.parse_args()
    
    # 載入模型
    if args.merged:
        model, tokenizer = load_merged_model(args.model_path, args.max_seq_length)
    else:
        model, tokenizer = load_model(args.model_path, args.base_model, args.max_seq_length)
    
    print(f"[INFO] Model loaded on {model.device}")
    
    if args.test_cases:
        run_test_cases(model, tokenizer)
    
    if args.interactive or (not args.test_cases and not args.interactive):
        interactive_chat(model, tokenizer)

if __name__ == "__main__":
    main()