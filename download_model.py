from chromadb.utils import embedding_functions

def download_embedding_model():
    print("開始下載/驗證本地 RAG 嵌入模型 (all-MiniLM-L6-v2)...")
    try:
        # Initializing the embedding function automatically triggers the download 
        # and caches it in the local HuggingFace cache folder (~/.cache/huggingface).
        embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        print("✅ 模型下載與快取完成！系統已準備好在完全離線環境下執行 run.py。")
    except Exception as e:
        print(f"❌ 下載過程中發生錯誤: {e}")
        print("請確保您目前有網際網路連線。")

if __name__ == "__main__":
    download_embedding_model()
