import os
import chromadb
from chromadb.utils import embedding_functions
import PyPDF2

class RAGService:
    def __init__(self):
        # Initialize local ChromaDB client (stores data in the local filesystem)
        persist_directory = os.path.join(os.getcwd(), 'instance', 'chroma_db')
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use a lightweight sentence-transformer model for embeddings
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        # Get or create a collection for documents
        self.collection = self.client.get_or_create_collection(
            name="document_knowledge_base",
            embedding_function=self.sentence_transformer_ef
        )

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF or TXT files."""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        try:
            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            raise e
        return text

    def process_and_store_document(self, file_path: str, document_id: str):
        """Extract text, chunk it, and store in ChromaDB."""
        text = self.extract_text(file_path)
        if not text.strip():
            raise ValueError("No text could be extracted from the document.")

        # Simple chunking strategy (e.g., split by double newlines or chunks of 500 characters)
        # Here we do a simple overlap chunking
        chunk_size = 500
        overlap = 50
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if len(chunk.strip()) > 10:  # ignore tiny empty chunks
                chunks.append(chunk)

        # Prepare data for Chroma
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file_path, "document_id": document_id} for _ in chunks]

        # Add to collection
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return len(chunks)

    def query_knowledge_base(self, query_text: str, n_results: int = 3) -> list:
        """Query the vector database for relevant chunks."""
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Chroma returns lists of lists for query_texts
        if results and 'documents' in results and len(results['documents']) > 0:
            return results['documents'][0]
        return []

rag_service = RAGService()
