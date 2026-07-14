# AI-多維度智慧問答系統 (ICAP Release Package)

這是一套以 Python + Flask 建置的 AI 智慧問答與分析平台，專注於提供企業級安全環境與多維度資料處理 (智能問答、RAG 文件解析、案件追蹤、心情解析)。

---

## 1. 主要功能

### 1.1 RAG (檢索增強生成) 文件解析
- 我在 app/services/rag_service.py 中看到了完整的實作，確實使用了 chromadb 作為本地向量庫，並利用 PyPDF2 讀取 PDF 進行切塊，最後透過 sentence-transformers 轉換向量，保證資料不連網。

### 1.2 智能問答 (Ollama)
- 在 app/services/gemini_service.py 中，程式確實是透過 urllib.request 直接打到本地端的 http://localhost:11434 呼叫 Ollama 進行推論。

### 1.3 企業級安全機制（離線執行）
- 在啟動檔 run.py 最上方，我看到程式強制寫入了 os.environ['HF_HUB_OFFLINE'] = '1' 以及 HF_HUB_DISABLE_TELEMETRY，完美阻擋了 HuggingFace 的對外連線與擾人的進度條。

---

## 2. 啟動方式與裝機 SOP

### 2.1 基礎環境準備（客戶電腦）
1. **安裝 Python**：至 [Python 官網](https://www.python.org/downloads/) 下載 Python 3.10+，並於安裝時**務必勾選「Add Python to PATH」**。
2. **安裝 Ollama 與模型**：
   - 至 [Ollama 官網](https://ollama.com/) 下載並安裝 Windows 版。
   - 於命令提示字元 (cmd) 執行 `ollama run gemma4` 下載預設語言模型。
3. **資料庫設定 (視情況)**：
   - 預設使用輕量級 SQLite，不需額外設定。
   - 若企業客戶使用 MSSQL，請確認安裝 SQL Server 與 ODBC Driver 18，並於 SSMS 新增 `complaint_db` 空白資料庫。

### 2.2 部署與初始化 (首次裝機必做)
1. 將裝機包解壓縮至客戶端電腦。
2. 若使用 MSSQL，請編輯 `.env` 修改 `DATABASE_URL` 連線字串。
3. 於資料夾空白處開啟 PowerShell 或終端機，依序執行下列指令：

```bash
# 1. 安裝所有核心套件
py -m pip install -r requirements.txt

# 2. 建立資料表與預設管理員帳號
py setup_user.py

# 3. 下載本地 RAG 嵌入模型 (避免無網路環境報錯)
py download_model.py
```

### 2.3 日常啟動
完成上述初始化後，日常運作或展示時，僅需啟動後端伺服器：

```bash
py run.py
```
> **提示**：系統已升級為 Waitress 生產級伺服器，啟動後終端機不會洗版顯示 HTTP 連線紀錄 (如 302/304)，以維持畫面專業與整潔。

後端預設位址：
`http://127.0.0.1:5000`

---

## 3. 初始管理員

首次啟動資料庫 (`setup_user.py`) 後，系統會自動建立一組最高權限帳號供出差裝機測試與交接使用：

- **帳號**：`admin`
- **密碼**：`admin`

> ⚠️ 若後續客戶遺忘密碼，可執行 `py reset_admin_password.py` 來強制重置管理員密碼。

---

## 4. 技術棧

### 後端
- Runtime：Python 3.10+
- Framework：Flask 3.0.3
- WSGI Server：Waitress (生產級)
- Database：SQLite / MSSQL
- ORM：Flask-SQLAlchemy 3.1.1

### AI 與數據處理
- LLM Inference：Ollama (透過 `google-genai` 呼叫)
- Vector DB：ChromaDB
- Embeddings：`sentence-transformers`
- Data Processing：Pandas, PyPDF2

---

## 5. 專案結構

```text
ICAP_Release_Package/
├── app/                      # 後端核心邏輯與藍圖 (Blueprints)
├── instance/                 # 本地資料庫目錄 (含 complaints.db)
├── static/                   # 靜態資源 (CSS, JS, 圖片)
├── templates/                # 前端 HTML 樣板
├── .env                      # 系統環境變數設定
├── download_model.py         # RAG 離線模型下載腳本
├── install.py                # 自動化安裝輔助腳本
├── README.md                 # 系統說明文件
├── requirements.txt          # Python 依賴套件清單
├── reset_admin_password.py   # 管理員密碼重置工具
├── run.py                    # 系統啟動入口 (使用 Waitress)
└── setup_user.py             # 資料庫與帳號初始化腳本
```

---

## 6. 疑難排解

### Q1. 執行 `py` 指令時出現「無法辨識的詞彙」或「找不到指令」
- 確認安裝 Python 時是否有勾選「Add Python to PATH」。
- 解決方式：請重新執行 Python 安裝程式，選擇 `Modify` 並勾選相關選項。

### Q2. 資料庫連線失敗 / Server 崩潰
- 若使用 MSSQL，檢查 `.env` 中的 `DATABASE_URL` 是否填寫正確，以及客戶端電腦是否有 `ODBC Driver 18 for SQL Server`。
- 確認 SQL Server 服務已啟動。

### Q3. 為什麼終端機看不到任何存取紀錄 (如 200/302/304)？
- 本系統基於效能與介面整潔考量，已將測試環境的 Flask Server 汰換為正式生產級的 Waitress Server。
- 此為正常現象，只有在程式發生未預期錯誤時，終端機才會顯示紅字日誌。
