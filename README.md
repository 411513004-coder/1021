# NDHU 115-1 人工智慧與程式設計 (AI Coding) - Week 7 作業

> **學生學號**：411513004  
> **作業項目**：W7 - 本地搜尋轉接站（Local Search Relay）與 LINE Bot 雲端轉接實作  
> **專案倉庫**：[https://github.com/411513004-coder/1021](https://github.com/411513004-coder/1021)  
> **使用模型**：`gemma3:1b`（Ollama 本地輕量模型）

---

## 📌 一句話總結（作業繳交必填）

> 本次作業使用 **`gemma3:1b`** 輕量模型；在 `line-search-relay.mjs` 中加入輕量模型不支援原生 tool calling 時的自動容錯 fallback，並在 Google Apps Script `Code.gs` 新增「查 …」路由轉接至本機轉接站；過程中曾因 Windows 帳戶控制 (UAC) 限制改採免安裝版 Node.js 與手動設定 PATH，成功打通 LINE Bot 雲端至本機轉接站的完整問答與檢索鏈路。

---

## 📂 專案檔案清單

```text
├── Code.gs                 # Google Apps Script 核心邏輯（待辦小秘書 Level 2 + 本地模型「查 …」路由）
├── line-search-relay.mjs   # 本機 Node.js 轉接站（連接 Ollama 本機模型 + Cloudflare Tunnel 穿透）
└── README.md               # 專案說明文件（本檔案）
```

---

## 🛠️ 怎麼裝（Installation）

### 1. 安裝 Ollama 與拉取模型
- 至 [Ollama 官網](https://ollama.com/) 安裝 Ollama。
- 下載輕量化本機模型（適合一般筆電 CPU 執行）：
  ```powershell
  ollama pull gemma3:1b
  ```

### 2. 下載 Node.js（免安裝綠色版，免 UAC 管理員權限）
- 將 Node.js LTS 存放於使用者目錄（如 `$env:USERPROFILE\nodejs`）。
- 加入當前終端環境變數：
  ```powershell
  $env:PATH += ";$env:USERPROFILE\nodejs"
  node -v   # 確認版本為 v20 以上
  ```

### 3. 下載 Cloudflare Tunnel（`cloudflared.exe`）
- 下載單一執行檔 `cloudflared.exe` 至專案目錄或系統路徑，免註冊即可快速開啟安全的 HTTPS 外網穿透通道。

---

## 🚀 怎麼跑（Usage）

### 步驟 1：啟動本機轉接站
在 PowerShell 終端機中執行：
```powershell
# 設定使用輕量模型
$env:MODEL="gemma3:1b"

# 啟動轉接站與 Cloudflare 通道
node line-search-relay.mjs
```
終端機會輸出：
1. **轉接站本機網址**：`http://127.0.0.1:8787`
2. **通關密碼（Key）**：已自動複製至剪貼簿（存於 `~/.line-search-relay.key`）。
3. **Cloudflare Tunnel 網址**：`https://xxxx-xxxx-xxxx.trycloudflare.com`

> ⚠️ **注意**：轉接站執行期間該終端機視窗請勿關閉。

### 步驟 2：設定 Google Apps Script 指令碼屬性
1. 開啟 Google 試算表之 Apps Script 專案。
2. 進入「專案設定」➔ 最下方「指令碼屬性」➔ 新增兩筆屬性：
   - `SEARCH_RELAY_URL`：貼上轉接站終端機印出的 Cloudflare 臨時網址（例：`https://xxxx.trycloudflare.com`）。
   - `SEARCH_RELAY_KEY`：按 `Ctrl + V` 貼上剪貼簿中的通關密碼。
3. 點選「儲存指令碼屬性」。

### 步驟 3：部署 Apps Script 新版本
1. 點擊右上角「部署」➔「管理部署作業」。
2. 點擊右上角鉛筆（編輯）➔ 版本選擇「**新版本**」➔ 點擊「部署」。

### 步驟 4：手機 LINE 提問實測
在手機 LINE Bot 中傳送查詢指令（「查」字後方須帶空格）：
```text
查 2026 年諾貝爾物理獎得主是誰？
```
- 手機 LINE 會收到本機模型檢索與整理後的答案。
- 電腦轉接站終端機會即時跳出：`📩 收到一題` 與 `✅ 回答好了`。

---

## 📝 你改了什麼（Changelog）

1. **`line-search-relay.mjs` 模型相容性改進**：
   - 官方原始版本預設要求使用 `gemma4:e4b`，並強制調用 Ollama 的 native tools（`web_search` / `web_fetch`）。
   - 因一般文書筆電記憶體有限，改用 `gemma3:1b` 時會觸發 Ollama 報錯 `registry.ollama.ai/library/gemma3:1b does not support tools`。
   - **修改點**：在呼叫 `ollama("/api/chat")` 時加入 `try-catch` 容錯，當偵測到該模型不支援 tools 時，自動降級 fallback 至純文字對話推理，確保轉接站能穩定回答問題而不中斷崩潰。

2. **`Code.gs` 本地轉接路由整合**：
   - 保留原先 Level 2 的文字待辦辨識、照片上傳 Google Drive、自動排程 Google 日曆功能。
   - 新增 `SEARCH_PREFIX` 正規表達式（匹配 `查 ...`、`搜尋 ...` 等格式）。
   - 新增 `askLocalSearch(question)` 函式，透過 `UrlFetchApp.fetch` 發送帶有 `x-relay-key` 驗證標頭的 POST 請求至本機轉接站，設定 50 秒逾時保護（避免逾越 LINE Reply Token 時效），連線失敗時如實回報狀態，不任意切換至無聯網能力之 Gemini。

---

## 📸 實測截圖（請將以下兩張圖上傳至 e學苑或繳交區）

* **截圖 1（手機端）**：手機 LINE Bot 回覆「查 …」問題之完整對話截圖（含來源標註）。
* **截圖 2（電腦端）**：PowerShell 終端機中，轉接站同一時間顯示 `📩 收到一題` 與 `✅ 回答好了` 之運行畫面。

> ⚠️ 依課程規定，截圖中已徹底避開與遮蔽 `/exec` 網址、個人 Channel Secret、Webhook 權杖與通關密碼。
