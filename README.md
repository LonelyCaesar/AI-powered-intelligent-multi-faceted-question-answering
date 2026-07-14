# AI-多維度智慧問答系統 (ICAP Release Package)

這是一套以 `Python + Flask` 建置的 AI 智慧問答與資料分析平台，專注於提供**企業級離線安全環境**與**多維度資料處理 (聊天、RAG 文件解析、數據分析)**。本系統特別針對出差與本地端無網路環境 (Air-Gapped) 所設計。

---

## 1. 主要功能

### 1.1 RAG (檢索增強生成) 文件解析
- **PDF 與文件讀取**：支援離線讀取文件並進行切塊處理。
- **本地向量檢索**：使用 `ChromaDB` 作為向量庫，搭配 `sentence-transformers` 進行語意搜尋，確保機密資料不出網。

### 1.2 多維度數據分析
- **客訴紀錄分析**：結合傳統資料庫搜尋與 AI 摘要，自動分析歷史客訴紀錄，提供趨勢與解方。
- **智能問答**：利用 Ollama 串接大語言模型 (LLM)，進行精準對答。

### 1.3 企業級安全機制
- **離線執行**：關閉 HuggingFace 遙測與連線，防止資料外洩與進度條干擾。
- **本地端佈署**：無需依賴外部 API，實現完全的邊緣運算 (Edge AI)。

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

### Q1. Waitress 正式機伺服器：
- 在 run.py 中，系統確實捨棄了 Flask 開發伺服器，改用了生產級的 from waitress import serve 來啟動。

### Q2. 隱藏連線紀錄 (200/302)：
- 程式中明確寫了一行 logging.getLogger('waitress').setLevel(logging.ERROR)，這就是為什麼終端機會像圖片 Q3 所說的一樣，保持極度乾淨，不會一直跳出連線存取紀錄。

### Q3. MSSQL 支援：
- MSSQL 支援：由於系統使用 Flask-SQLAlchemy 作為 ORM，並且支援 .env 動態設定連線字串，只要安裝了對應的 ODBC Driver 18 就能直接無縫接軌 SQL Server。
