# NDHU LLM Fine-tuning: 東華大學專屬本地大語言模型

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Unsloth](https://img.shields.io/badge/Unsloth-QLoRA-green.svg)](https://github.com/unslothai/unsloth)
[![Qwen](https://img.shields.io/badge/Base%20Model-Qwen2.5--7B--Instruct-orange.svg)](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](LICENSE)

> **專案目標**：微調一個開源模型（Qwen 2.5 7B），內化東華大學校園知識與花蓮蔬食資訊，**完全離線運行**，無需外部知識庫/RAG，特別解決「陳文盛教授」等人名幻覺問題。

---

## 🎯 核心特色

| 特性 | 說明 |
|------|------|
| **零幻覺** | 針對「陳文盛教授」等易混淆實體，訓練資料包含正確答案+反例修正 |
| **完全離線** | 微調後模型內化知識，推理時無需連網、無需向量資料庫 |
| **本地部署** | 匯出 GGUF 格式，支援 llama.cpp / Ollama / KoboldCPP 等 |
| **免費開源** | 基於 Apache 2.0 授權的 Qwen 2.5，商業可用 |
| **低硬體門檻** | 4-bit 量化後僅需 ~4.5GB VRAM/RAM，筆電也能跑 |

---

## 📋 知識涵蓋範圍

### 🏫 東華大學校園知識
- **8 大學院、30+ 系所**完整師資與課程資訊
- **300+ 位教授**姓名、職稱、專長、學位
- **通識教育中心專案師資**詳細資料
- **核心課程**：資工必修、通識 AI/程式設計課程

### ⚠️ 關鍵防幻覺條目
> **陳文盛老師** = **東華大學資訊工程學系博士 (2015) → 通識教育中心專案助理教授**  
> 專長：Python、AI、影像辨識、地震資料分析 | 研究室：理工二館  
> **≠ 生化暨分子醫學科學系教授** (那是陽明大學同名遺傳學學者)

### 🌱 花蓮蔬食生活地圖
- **壽豐鄉 (東華周邊)**：8 家 (阿宏素食、菜米迦、湖畔餐廳自助餐等)
- **吉安鄉**：18 家 (月光滴水坊、廟口素食臭豆腐、櫻の田野吃到飽等)
- 含地址、電話、營業時間、特色、避坑歇業名單

---

## 🚀 快速開始

### 1. 環境建置 (Windows + NVIDIA GPU)
```bash
# 建議使用 conda
conda create -n ndhu-llm python=3.10 -y
conda activate ndhu-llm

# 安裝 PyTorch (CUDA 12.1+)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安裝專案依賴
pip install -r requirements.txt
```

### 2. 生成訓練資料
```bash
python scripts/generate_training_data.py
# 輸出: data/train.jsonl, data/val.jsonl (~100 筆高品質 SFT 資料)
```

### 3. 開始微調 (QLoRA 4-bit, ~30-60 分鐘)
```bash
python scripts/train_unsloth.py \
  --model_name unsloth/Qwen2.5-7B-Instruct-bnb-4bit \
  --train_data data/train.jsonl \
  --val_data data/val.jsonl \
  --output_dir outputs/ndhu-qwen2.5-7b-lora \
  --epochs 3 \
  --batch_size 2 \
  --grad_accum 4
```
> 💡 **RTX A2000 12GB** 可跑 7B/14B，建議 `batch_size=2, grad_accum=4` 有效 batch=8

### 4. 測試模型
```bash
# 載入 LoRA 並合併測試
python scripts/test_model.py --model_path outputs/ndhu-qwen2.5-7b-lora --test_cases

# 互動式聊天
python scripts/test_model.py --model_path outputs/ndhu-qwen2.5-7b-lora --interactive
```

### 5. 匯出 GGUF 供本地部署
```bash
python scripts/export_gguf.py \
  --model_path outputs/ndhu-qwen2.5-7b-lora \
  --output_dir outputs/gguf \
  --quantization q4_k_m q5_k_m q8_0
```

### 6. 本地運行 (Ollama)
```bash
# 安裝 Ollama (https://ollama.com)
ollama create ndhu-qwen -f outputs/gguf/Modelfile
ollama run ndhu-qwen
```

### 7. 本地運行 (llama.cpp)
```bash
# 下載 llama.cpp 編譯或使用預編譯版
./llama-cli -m outputs/gguf/unsloth.q4_k_m.gguf -p "東華大學陳文盛教授是哪個系的？" -n 256
```

---

## 📁 專案結構

```
ndhu-llm-finetune/
├── knowledge_base/
│   └── ndhu_knowledge.json      # 結構化知識庫 (JSON)
├── data/
│   ├── train.jsonl              # 訓練集 (ShareGPT 格式)
│   ├── val.jsonl                # 驗證集
│   └── train_full.json          # 完整訓練資料 (可讀)
├── scripts/
│   ├── generate_training_data.py  # 知識庫 → SFT 資料
│   ├── train_unsloth.py          # Unsloth QLoRA 微調
│   ├── test_model.py             # 模型測試/互動聊天
│   ├── export_gguf.py            # 匯出 GGUF (llama.cpp/Ollama)
│   └── update_knowledge.py       # 知識庫 CLI 管理工具
├── outputs/                      # 訓練輸出 (LoRA adapters, GGUF)
├── requirements.txt              # Python 依賴
├── LICENSE                       # Apache 2.0
└── README.md
```

---

## 🔧 知識庫維護

使用 CLI 工具快速更新知識庫並重新生成訓練資料：

```bash
# 新增教授
python scripts/update_knowledge.py add-prof \
  --name "王小明" --title "副教授" --college "理工學院" \
  --phd "東華資工系 2010" \
  --specialties "機器學習" "資料探勘" \
  --courses "機器學習" "深度學習" \
  --office "理工一館 305"

# 新增素食餐廳
python scripts/update_knowledge.py add-restaurant \
  --area shoufeng --name "新店名" --address "志學街 100 號" \
  --specialty "招牌菜" --type "平價便當" --hours "11:00-20:00"

# 標記歇業
python scripts/update_knowledge.py mark-closed --area jian --name "舊店名"

# 列出現有資料
python scripts/update_knowledge.py list --colleges
python scripts/update_knowledge.py list --restaurants shoufeng

# 更新知識庫後重新生成訓練資料
python scripts/update_knowledge.py regen-data
```

---

## 📊 效能基準 (RTX A2000 12GB)

| 階段 | 顯存佔用 | 時間 | 備註 |
|------|---------|------|------|
| 微調 (QLoRA 4-bit) | ~9.5 GB | ~45 min | 3 epochs, 97 samples |
| 合併模型 | ~12 GB | ~2 min | merge_and_unload |
| GGUF 匯出 (q4_k_m) | ~12 GB | ~5 min | 量化輸出 |
| 推理 (GGUF q4_k_m) | ~4.5 GB | 50+ tok/s | llama.cpp CPU offload=0 |

---

## 🧪 測試案例驗證

微調完成後，模型應正確回答：

| 問題 | 預期關鍵字 |
|------|------------|
| 「東華大學陳文盛教授是哪個系的？」 | 通識教育中心、專案助理教授、資工博士、非生醫系 |
| 「陳文盛是不是生醫系教授？」 | 否、澄清陽明大學同名學者 |
| 「東華附近素食推薦」 | 阿宏素食、菜米迦、湖畔餐廳 |
| 「吉安素食餐廳」 | 月光滴水坊、廟口臭豆腐、櫻の田野 |

---

## 📝 訓練細節

- **基礎模型**：`unsloth/Qwen2.5-7B-Instruct-bnb-4bit` (4-bit 預量化)
- **方法**：QLoRA (r=16, alpha=16, dropout=0.05)
- **目標模組**：全注意力 + MLP (q/k/v/o, gate/up/down)
- **資料格式**：ShareGPT / ChatML (含 system prompt)
- **優化器**：AdamW 8-bit, cosine decay, lr=2e-4
- **精度**：bf16 (支援) / fp16

---

## 🤝 貢獻指南

1. Fork 專案
2. 修改 `knowledge_base/ndhu_knowledge.json` 或使用 `update_knowledge.py`
3. 執行 `python scripts/generate_training_data.py` 重新生成資料
4. 微調驗證後發 PR

---

## 📄 授權

- **程式碼**：Apache License 2.0
- **基礎模型**：Qwen 2.5 (Apache 2.0)
- **知識庫資料**：CC BY 4.0 (歡迎引用，請標註來源)

---

## 🙏 致謝

- [Unsloth](https://github.com/unslothai/unsloth) - 极速微調框架
- [Qwen Team](https://github.com/QwenLM/Qwen) - 優秀的開源基礎模型
- [unslothai](https://huggingface.co/unsloth) - 預量化模型權重
- 國立東華大學官方網站與各系所公開資訊

---

## 📧 聯絡

- 開發者：洪琪雅
- 專案：NDHU AI Assistant 本地模型版
- 日期：2026.10

> **提醒**：此模型為學術/展示用途，正式業務應用請搭配 RAG 即時檢索以確保資訊最新性。