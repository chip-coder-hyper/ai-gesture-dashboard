import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self):
        # Máy băm văn bản vẫn giữ nguyên cấu hình chuẩn
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def process_document(self, file_path: str):
        """
        Phiên bản nâng cấp: Tự động nhận diện và đọc file PDF, DOCX, TXT.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Lỗi: Không tìm thấy file tại {file_path}")

        # Lấy đuôi file (ví dụ: '.pdf', '.docx') và chuyển thành chữ thường để so sánh
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            # --- CHIẾN LƯỢC CHỌN CÔNG CỤ ĐỌC DỰA VÀO ĐUÔI FILE ---
            if file_extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            elif file_extension == ".txt":
                # File txt yêu cầu thêm mã hóa utf-8 để không bị lỗi font tiếng Việt
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                raise ValueError(f"Hệ thống chưa hỗ trợ định dạng file: {file_extension}")

            # Tiến hành đọc toàn bộ chữ trong file
            documents = loader.load()

            # Băm nhỏ tài liệu thành các chunks
            chunks = self.text_splitter.split_documents(documents)
            
            return chunks
        except Exception as e:
            raise Exception(f"Lỗi hệ thống khi xử lý file {file_extension}: {str(e)}")