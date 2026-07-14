import pandas as pd
import os
from app.services.gemini_service import gemini_service

class DataAnalyzerService:
    def analyze_csv(self, file_path: str, user_query: str) -> dict:
        """Analyze a CSV file based on the user's query."""
        try:
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            else:
                return {"response": "不支援的檔案格式，請上傳 CSV 或 Excel 檔案。", "suggestions": ["支援哪些格式？"]}
                
            # Get basic info about the dataframe to provide context to the LLM
            columns = ", ".join(df.columns.tolist())
            row_count = len(df)
            head_data = df.head(5).to_string()
            summary_stats = df.describe(include='all').to_string()
            
            # Construct a prompt for the LLM
            prompt = f"""
            你是一位專業的數據分析師。使用者上傳了一份數據表格，並提出了一個問題。
            請根據以下表格的結構與摘要統計資訊，回答使用者的問題。
            
            【表格資訊】
            - 欄位名稱: {columns}
            - 總資料筆數: {row_count}
            
            【前 5 筆資料預覽】
            {head_data}
            
            【摘要統計】
            {summary_stats}
            
            使用者問題: {user_query}
            
            請針對使用者的問題進行分析與回答。在回覆的最後，請務必提供三個與這份數據相關的延伸問題。
            請嚴格依照以下格式輸出，不要有任何偏差：
            
            (你的回覆內容)
            
            ===SUGGESTIONS===
            1. (延伸問題1)
            2. (延伸問題2)
            3. (延伸問題3)
            """
            
            # Use gemini_service (Ollama) to generate the response based on the prompt
            full_response = gemini_service._call_ollama(prompt)
            
            if "===SUGGESTIONS===" in full_response:
                parts = full_response.split("===SUGGESTIONS===")
                response_text = parts[0].strip()
                suggestions_text = parts[1].strip()
                import re
                suggestions = re.findall(r'\d+\.\s*(.+)', suggestions_text)
                suggestions = [s.replace('**', '').replace('*', '').strip() for s in suggestions]
                if not suggestions:
                    suggestions = ["請提供更多數據細節", "有哪些明顯的趨勢？", "這份資料還能分析什麼？"]
                return {"response": f"[數據分析報告]\n\n{response_text}", "suggestions": suggestions[:3]}
            else:
                return {"response": f"[數據分析報告]\n\n{full_response}", "suggestions": ["請提供更多數據細節", "有哪些明顯的趨勢？", "這份資料還能分析什麼？"]}
                
        except Exception as e:
            return {"response": f"【數據分析錯誤】無法解析或分析檔案。錯誤細節: {str(e)}", "suggestions": ["請重新上傳檔案", "確認表格格式是否正確"]}

data_analyzer_service = DataAnalyzerService()
