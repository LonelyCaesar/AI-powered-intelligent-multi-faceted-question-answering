# 🚀 Enterprise GenAI Customer Support & Analytics Platform
### 企業級 AI 智能客服與輿情分析中控台

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange)
![Status](https://img.shields.io/badge/Status-MVP-success)

## 📖 專案簡介 (Project Overview)
本專案為一個 **AI 應用工程 (AI Application Engineering)** 的實戰作品。
解決了傳統客服系統「數據非結構化」與「回應被動」的痛點。系統整合 **Google Gemini LLM**，建立了一套自動化的 ETL 流程，能即時將客戶的自然語言轉化為結構化的情緒指標，並透過動態儀表板輔助決策。

## 🛠️ 技術架構 (Tech Stack)
- **AI Core**: Google Generative AI SDK (Gemini 1.5 Flash).
- **Prompt Engineering**: 實作 Few-Shot & Structured Prompting 以確保輸出格式穩定。
- **Backend**: Python, Flask (RESTful API Design).
- **Frontend**: Bootstrap 5, JavaScript (Async/Await), Chart.js.
- **Data**: SQLite, SQLAlchemy (ORM).

## ✨ 核心功能 (Key Features)
1.  **🤖 GenAI 智能對話**：串接 Gemini API，實現低延遲的智慧問答。
2.  **🧠 自動化輿情分析**：
    - **[技術亮點]** 使用 LLM 解析非結構化文本，提取 `情緒分數 (1-10)` 與 `關鍵意圖`。
    - 自動生成「安撫性回覆草稿」，實現 Human-in-the-loop 協作流程。
3.  **📊 即時數據中台**：
    - 使用 Chart.js 視覺化工單狀態 (Pending vs Resolved)。
    - 實作 AJAX 輪詢機制，確保數據即時性。

## 🚀 快速啟動 (Quick Start)

1. **安裝依賴**
   ```bash
   pip install -r requirements.txt