import os
import json
import urllib.request
import urllib.error
import uuid
from app.services.rag_service import rag_service

class GeminiAPIError(Exception):
    """Custom exception for AI API errors (now pointing to Ollama)."""
    pass

class GeminiService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self._initialize_client()

    def _initialize_client(self):
        self.model = os.getenv("OLLAMA_MODEL", "gemma4")
        print(f"Initializing AI Service with Ollama Model: {self.model}")

    def _call_ollama(self, prompt: str) -> str:
        data = {
            "model": self.model,
            "prompt": prompt,
            "system": "你是一個專業的台灣 AI 助理。請務必使用「繁體中文（zh-TW）」回答所有問題，絕對不能使用簡體中文。",
            "stream": False
        }
        req = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
        except urllib.error.URLError as e:
            raise GeminiAPIError(f"無法連線到本地 Ollama 伺服器 (http://localhost:11434)。請確認 Ollama 已啟動。錯誤: {e.reason}")
        except Exception as e:
            raise GeminiAPIError(f"Ollama 回應發生錯誤: {str(e)}")

    def generate_chat_response(self, message: str) -> dict:
        prompt = f"""
        使用者訊息: {message}
        
        請回覆使用者的訊息。在回覆的最後，請務必提供三個與上述對話相關的延伸問題（也就是使用者可以接著問的問題），供使用者快速點選。
        請嚴格依照以下格式輸出，不要有任何偏差：
        
        (你的回覆內容)
        
        ===SUGGESTIONS===
        1. (延伸問題1)
        2. (延伸問題2)
        3. (延伸問題3)
        """
        try:
            full_response = self._call_ollama(prompt)
            if "===SUGGESTIONS===" in full_response:
                parts = full_response.split("===SUGGESTIONS===")
                response_text = parts[0].strip()
                suggestions_text = parts[1].strip()
                import re
                suggestions = re.findall(r'\d+\.\s*(.+)', suggestions_text)
                suggestions = [s.replace('**', '').replace('*', '').strip() for s in suggestions]
                if not suggestions:
                    suggestions = ["請提供更多細節", "這代表什麼意思？", "還有其他建議嗎？"]
                return {"response": response_text, "suggestions": suggestions[:3]}
            else:
                return {"response": full_response, "suggestions": ["請提供更多細節", "這代表什麼意思？", "還有其他建議嗎？"]}
        except GeminiAPIError as e:
            return {"response": f"【本地 AI 提示】{str(e)}", "suggestions": ["請提供更多細節", "這代表什麼意思？", "還有其他建議嗎？"]}

    def generate_rag_response(self, message: str, file_path: str) -> dict:
        """Generate response based on a document (RAG)."""
        try:
            # Generate a temporary document ID
            doc_id = str(uuid.uuid4())
            
            # 1. Process and store the document in local ChromaDB
            rag_service.process_and_store_document(file_path, doc_id)
            
            # 2. Retrieve relevant context for the user's message
            context_chunks = rag_service.query_knowledge_base(message, n_results=3)
            context = "\n\n".join(context_chunks)
            
            if not context:
                context = "無法從文件中擷取有效內容。"
                
            prompt = f"""
            你是一個專業的 AI 助理。請根據以下提供參考文件內容，回答使用者的問題。
            如果參考文件內容無法回答該問題，請誠實告知，不要自行編造。
            
            參考文件內容：
            {context}
            
            使用者訊息：{message}
            
            請回覆使用者的訊息。在回覆的最後，請務必提供三個與上述對話相關的延伸問題。
            請嚴格依照以下格式輸出，不要有任何偏差：
            
            (你的回覆內容)
            
            ===SUGGESTIONS===
            1. (延伸問題1)
            2. (延伸問題2)
            3. (延伸問題3)
            """
            
            full_response = self._call_ollama(prompt)
            if "===SUGGESTIONS===" in full_response:
                parts = full_response.split("===SUGGESTIONS===")
                response_text = parts[0].strip()
                suggestions_text = parts[1].strip()
                import re
                suggestions = re.findall(r'\d+\.\s*(.+)', suggestions_text)
                suggestions = [s.replace('**', '').replace('*', '').strip() for s in suggestions]
                if not suggestions:
                    suggestions = ["請提供更多細節", "這代表什麼意思？", "這份文件還有什麼重點？"]
                return {"response": f"[從文件中找到的解答]\n\n{response_text}", "suggestions": suggestions[:3]}
            else:
                return {"response": f"[從文件中找到的解答]\n\n{full_response}", "suggestions": ["請提供更多細節", "這代表什麼意思？", "這份文件還有什麼重點？"]}
                
        except Exception as e:
            return {"response": f"【檔案處理錯誤】{str(e)}", "suggestions": ["請重新上傳檔案", "這代表什麼意思？", "還有其他建議嗎？"]}

    def analyze_sentiment(self, text: str) -> str:
        prompt = f"""
        你是一位資深客服數據分析師。請分析以下客訴內容：
        "{text}"
        
        （注意：文字開頭若有標示「[顧客心情：(表情圖示)]」，代表顧客自行選擇了當下的心情，請務必將此表情圖示納入情緒分數與情緒標籤的綜合評估中。）

        請嚴格依照以下格式回傳結果 (Plain Text Only，不要使用 Markdown 語法)：
        情緒分數：(1-10分，10為最憤怒)
        情緒標籤：(例如：憤怒、失望、焦慮、平靜)
        關鍵訴求：(一句話摘要)
        建議回覆：(50字以內的專業安撫回覆)
        """
        try:
            return self._call_ollama(prompt)
        except GeminiAPIError as e:
            return f"情緒分數：5\n情緒標籤：本地系統錯誤\n關鍵訴求：無法連線至 Ollama\n建議回覆：【系統提示】請檢查本地 Ollama 服務是否已經啟動，或是模型 ({self.model}) 是否正確載入。"

    def analyze_chat(self, original_complaint: str, analysis_result: str, chat_history: list, new_question: str) -> str:
        history_text = ""
        for msg in chat_history:
            role = "使用者" if msg.get('role') == 'user' else "AI 客服顧問"
            history_text += f"{role}: {msg.get('content')}\n\n"
            
        prompt = f"""
        你現在是一位資深客服管理顧問。
        以下是一份客戶抱怨的原始內容，以及你稍早對這份客訴作出的初步分析結果。
        使用者現在對這份分析結果或原客訴事件有進一步的提問。請根據上下文，提供專業、具體且可執行的建議或解答。

        【原始客訴內容】：
        "{original_complaint}"
        
        【初步分析結果】：
        "{analysis_result}"
        
        【歷史問答紀錄】：
        {history_text if history_text else "(無)"}
        
        【使用者最新提問】：
        "{new_question}"
        
        請直接回傳你的解答，不需要重複使用者的問題，也不要加上「好的」、「回答如下」等冗言贅字。
        """
        try:
            return self._call_ollama(prompt)
        except GeminiAPIError as e:
            return f"追問失敗：{str(e)}"

    def refine_complaint_text(self, text: str) -> str:
        prompt = f"""
        你現在是一個專業的客服與問題回報撰寫專家。請將以下客戶簡短或口語的描述，擴充、修改成一段「完整且專業的客服問題描述 (Problem Description)」。
        例如，如果使用者說：「這個東西很老不怎麼用」，你應該擴充成類似：「客戶反映目前使用的設備/產品款式較為老舊，且日常使用頻率不高，希望能提供相關的更新建議或替代方案...」等完整描述。

        原始輸入：
        "{text}"
        
        請直接回傳修改後、擴充完整的文字段落，不要包含任何額外的問候語、解釋，也不要加上「好的」、「擴充如下」等冗言贅字。
        """
        try:
            return self._call_ollama(prompt)
        except GeminiAPIError as e:
            return text

    def refine_reply_text(self, original_complaint: str, draft_reply: str) -> str:
        prompt = f"""
        你現在是一位專業、有禮貌且善解人意的客服人員。
        以下是客戶反映的問題描述，以及客服人員初步草擬的簡短回覆。
        請根據客戶的問題，將草擬的簡短回覆擴充、潤飾成一段「完整且專業的正式回覆 (Professional Reply)」。
        必須保持友善、同理心，並且具體回應客戶的訴求。

        【客戶反映的問題描述】：
        "{original_complaint}"
        
        【客服人員初步草擬的回覆】：
        "{draft_reply}"
        
        請直接回傳修改後、擴充完整的最終回覆內容，不要包含任何額外的解釋，也不要加上「好的」、「修改如下」等冗言贅字。
        """
        try:
            return self._call_ollama(prompt)
        except GeminiAPIError as e:
            return draft_reply

# Singleton instance
gemini_service = GeminiService()

