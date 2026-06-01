import os

# --- TẮT THEO DÕI CỦA CHROMADB ĐỂ DỌN SẠCH TERMINAL ---
os.environ["CHROMA_TELEMETRY"] = "false" 

# --- SỬ DỤNG CÁC GÓI THƯ VIỆN CHUẨN MỚI NHẤT ---
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class VectorDBManager:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.persist_directory = persist_directory
        
        # Mô hình nhúng (Embedding) - Biến chữ thành số
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Khởi tạo cơ sở dữ liệu Vector cục bộ
        self.db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model
        )

    def add_documents(self, chunks):
        """Mã hóa các đoạn văn bản (chunks) thành vector và lưu vào DB"""
        self.db.add_documents(chunks)

    def search(self, query: str, k: int = 2):
        """Tìm kiếm k đoạn văn bản có ý nghĩa sát với câu hỏi nhất"""
        return self.db.similarity_search(query, k=k)