#!/usr/bin/env python3
"""
將微調後的模型匯出為 GGUF 格式
支援 llama.cpp、Ollama、KoboldCPP 等本地推理引擎
"""
import argparse
import os
from unsloth import FastLanguageModel

def export_gguf(model_path, output_dir, base_model="unsloth/Qwen2.5-7B-Instruct",
                quantization_methods=None):
    """
    匯出 GGUF 格式
    
    量化方法說明：
    - q4_k_m: 平衡品質與大小 (推薦，~4.5GB)
    - q5_k_m: 較高品質 (~5.5GB)  
    - q8_0: 高品質 (~8GB)
    - f16: 無量化 (~14GB)
    """
    if quantization_methods is None:
        quantization_methods = ["q4_k_m", "q5_k_m", "q8_0"]
    
    print(f"[INFO] Loading model from: {model_path}")
    print(f"[INFO] Base model: {base_model}")
    
    # 載入合併後的模型 (需要完整精度)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=False,  # 匯出 GGUF 需要完整精度
    )
    
    # 載入 LoRA 並合併
    from peft import PeftModel
    print("[INFO] Loading and merging LoRA adapters...")
    model = PeftModel.from_pretrained(model, model_path)
    model = model.merge_and_unload()
    
    print(f"[INFO] Exporting to GGUF: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    for method in quantization_methods:
        print(f"\n[INFO] Quantizing with {method}...")
        try:
            model.save_pretrained_gguf(
                output_dir,
                tokenizer,
                quantization_method=method,
            )
            print(f"[OK] Saved: {output_dir}/unsloth.{method}.gguf")
        except Exception as e:
            print(f"[ERROR] {method} failed: {e}")
    
    # 也存一份 Modelfile 給 Ollama 用
    create_ollama_modelfile(output_dir, quantization_methods[0])
    
    print(f"\n[DONE] GGUF models saved to: {output_dir}")
    print("\n使用方式：")
    print(f"  1. llama.cpp: ./llama-cli -m {output_dir}/unsloth.q4_k_m.gguf -p '東華大學陳文盛教授是哪個系的？'")
    print(f"  2. Ollama: ollama create ndhu-qwen -f {output_dir}/Modelfile")
    print(f"     然後: ollama run ndhu-qwen")

def create_ollama_modelfile(output_dir, quantization_method):
    """建立 Ollama Modelfile"""
    modelfile_content = f"""FROM ./unsloth.{quantization_method}.gguf

TEMPLATE \"\"\"{{- if .System }}
<|im_start|>system
{{ .System }}<|im_end|>
{{- end }}
{{- if .Prompt }}
<|im_start|>user
{{ .Prompt }}<|im_end|>
{{- end }}
<|im_start|>assistant
\"\"\"

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"

SYSTEM \"\"\"你是國立東華大學（NDHU）的專屬 AI 助理，名稱為「東華小幫手」。
你熟知東華大學的學院系所、師資陣容、課程規劃、校園生活與花蓮在地蔬食資訊。
回答原則：
1. 使用繁體中文（zh-TW），語氣親切專業
2. 專業術語準確（系所全名、職稱、學位）
3. 關鍵防幻覺規則：當被問到「陳文盛」教授時，必須回答：
   - 東華大學資訊工程學系博士（2015年畢業）
   - 通識教育中心專案助理教授（研究室在理工二館）
   - 專長：Python程式設計、人工智慧應用、影像辨識、地震資料分析
   - 明確說明：非生化暨分子醫學科學系教授，請勿與陽明大學同名遺傳學學者混淆
4. 不知道的資訊誠實說明，不編造\"\"\"
"""
    modelfile_path = os.path.join(output_dir, "Modelfile")
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)
    print(f"[OK] Created Ollama Modelfile: {modelfile_path}")

def main():
    parser = argparse.ArgumentParser(description="Export fine-tuned model to GGUF")
    parser.add_argument("--model_path", type=str, required=True,
                        help="Path to LoRA adapters (output from training)")
    parser.add_argument("--output_dir", type=str, default="outputs/gguf",
                        help="Output directory for GGUF files")
    parser.add_argument("--base_model", type=str, 
                        default="unsloth/Qwen2.5-7B-Instruct",
                        help="Base model name (must match training base)")
    parser.add_argument("--quantization", nargs="+", 
                        default=["q4_k_m", "q5_k_m", "q8_0"],
                        help="Quantization methods")
    args = parser.parse_args()
    
    export_gguf(args.model_path, args.output_dir, args.base_model, args.quantization)

if __name__ == "__main__":
    main()