#!/usr/bin/env python3
"""
Unsloth QLoRA 微調腳本
針對 Qwen 2.5 7B Instruct 進行微調
支援 4-bit 量化訓練，極度省顯存
"""
import os
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="NDHU Qwen 2.5 7B Fine-tuning with Unsloth")
    parser.add_argument("--model_name", type=str, default="unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
                        help="Base model (Unsloth 4-bit quantized versions recommended)")
    parser.add_argument("--train_data", type=str, default="data/train.jsonl",
                        help="Training data path (JSONL ShareGPT format)")
    parser.add_argument("--val_data", type=str, default="data/val.jsonl",
                        help="Validation data path")
    parser.add_argument("--output_dir", type=str, default="outputs/ndhu-qwen2.5-7b-lora",
                        help="Output directory for LoRA adapters")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                        help="Max sequence length")
    parser.add_argument("--batch_size", type=int, default=2,
                        help="Per device train batch size")
    parser.add_argument("--grad_accum", type=int, default=4,
                        help="Gradient accumulation steps")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of training epochs")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                        help="Learning rate")
    parser.add_argument("--lora_r", type=int, default=16,
                        help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=16,
                        help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05,
                        help="LoRA dropout")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--push_to_hub", action="store_true",
                        help="Push to Hugging Face Hub")
    parser.add_argument("--hub_model_id", type=str, default="",
                        help="HF Hub model ID (e.g. username/model-name)")
    return parser.parse_args()

def formatting_prompts_func(examples):
    """Format ShareGPT format to text for SFTTrainer"""
    convos = examples["messages"]
    texts = []
    for convo in convos:
        # Unsloth's apply_chat_template handles this
        text = tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return {"text": texts}

def main():
    args = parse_args()
    
    # 設定隨機種子
    torch.manual_seed(args.seed)
    
    print(f"[INFO] Loading model: {args.model_name}")
    print(f"[INFO] Max seq length: {args.max_seq_length}")
    print(f"[INFO] LoRA config: r={args.lora_r}, alpha={args.lora_alpha}, dropout={args.lora_dropout}")
    
    # 載入模型和 tokenizer (Unsloth 自動處理 4-bit 量化)
    global model, tokenizer
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        dtype=None,  # 自動偵測 (bf16/fp16)
        load_in_4bit=True,  # 4-bit 量化載入
    )
    
    # 加上 LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",  # 省顯存
        random_state=args.seed,
        use_rslora=False,
        loftq_config=None,
    )
    
    print(f"[INFO] Model loaded. Trainable params: {model.num_parameters(only_trainable=True):,}")
    print(f"[INFO] Total params: {model.num_parameters():,}")
    
    # 載入資料集
    print(f"[INFO] Loading dataset from {args.train_data}")
    dataset = load_dataset("json", data_files={
        "train": args.train_data,
        "validation": args.val_data
    })
    
    # 格式化資料
    print("[INFO] Formatting dataset...")
    dataset = dataset.map(
        formatting_prompts_func,
        batched=True,
        remove_columns=dataset["train"].column_names,
    )
    
    print(f"[INFO] Train samples: {len(dataset['train'])}")
    print(f"[INFO] Val samples: {len(dataset['validation'])}")
    
    # 訓練參數
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_steps=10,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=25,
        save_steps=25,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=args.seed,
        report_to="none",  # 關閉 wandb 等
        remove_unused_columns=False,
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        args=training_args,
        packing=False,  # 不打包，保持對話結構
    )
    
    print("[INFO] Starting training...")
    trainer_stats = trainer.train()
    
    print(f"[INFO] Training completed! Final loss: {trainer_stats.training_loss:.4f}")
    
    # 儲存 LoRA adapters
    print(f"[INFO] Saving LoRA adapters to {args.output_dir}")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # 也存一份合併後的模型 (可選，需要較多顯存)
    # print("[INFO] Saving merged model...")
    # model.save_pretrained_merged(args.output_dir + "_merged", tokenizer, save_method="merged_16bit")
    
    print("[INFO] Done! You can now:")
    print(f"  1. Test with: python scripts/test_model.py --model_path {args.output_dir}")
    print(f"  2. Export GGUF: python scripts/export_gguf.py --model_path {args.output_dir}")
    print(f"  3. Or merge: model.save_pretrained_merged('outputs/merged', tokenizer, save_method='merged_16bit')")
    
    # 推送到 HF Hub (可選)
    if args.push_to_hub and args.hub_model_id:
        print(f"[INFO] Pushing to HF Hub: {args.hub_model_id}")
        model.push_to_hub(args.hub_model_id)
        tokenizer.push_to_hub(args.hub_model_id)

if __name__ == "__main__":
    main()