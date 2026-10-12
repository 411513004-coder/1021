# 訓練資料說明

此目錄存放微調用的 SFT (Supervised Fine-Tuning) 資料。

## 檔案說明

| 檔案 | 格式 | 用途 |
|------|------|------|
| `train.jsonl` | JSONL (ShareGPT) | 訓練集，每行一筆對話 |
| `val.jsonl` | JSONL (ShareGPT) | 驗證集 |
| `train_full.json` | JSON (pretty) | 完整訓練資料，供人工檢視 |

## 資料格式 (ShareGPT / ChatML)

```json
{
  "messages": [
    {"role": "system", "content": "你是東華大學專屬 AI 助理..."},
    {"role": "user", "content": "東華大學陳文盛教授是哪個系的？"},
    {"role": "assistant", "content": "東華大學的陳文盛老師是通識教育中心專案助理教授..."}
  ]
}
```

## 資料統計

- **總筆數**：~100 筆 (含防幻覺、學院系所、課程、素食餐廳、通用校園資訊)
- **核心防幻覺 (陳文盛)**：13 筆 (含正確答案 10 筆 + 反例修正 3 筆)
- **學院系所**：71 筆
- **課程**：2 筆
- **素食餐廳**：8 筆
- **通用校園資訊**：3 筆
- **訓練/驗證分割**：90% / 10%

## 重新生成資料

修改 `knowledge_base/ndhu_knowledge.json` 後：

```bash
python scripts/generate_training_data.py
```

或使用 CLI 工具：

```bash
python scripts/update_knowledge.py regen-data
```

## 資料來源

- 東華大學官方網站各系所師資頁面
- 通識教育中心師資公告
- 花蓮縣政府觀光旅遊網
- 實地走訪驗證 (壽豐/吉安素食餐廳)
- Google Maps / 各餐廳官方粉絲專頁