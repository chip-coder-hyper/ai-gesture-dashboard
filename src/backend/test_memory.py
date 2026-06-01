import os
from services.document_processor import DocumentProcessor
from services.vector_db import VectorDBManager

# 1. Tạo nhanh một file text chứa thông tin giả lập để test
test_file = "thong_tin_test.txt"
with open(test_file, "w", encoding="utf-8") as f:
    f.write("Hải Long là một lập trình viên phần mềm đang hoàn thiện đồ án tốt nghiệp về AI.\n")
    f.write("Bên cạnh việc code, anh có niềm đam mê đặc biệt với việc setup bể cá thủy sinh (biotope) sử dụng lũa và cát suối.\n")
    f.write("Hệ thống RAG này được anh xây dựng bằng nền tảng FastAPI, Gemini 2.5 Flash và ChromaDB.\n")

try:
    print("1. Đang băm nhỏ tài liệu test...")
    processor = DocumentProcessor()
    chunks = processor.process_document(test_file)
    print(f"   -> Đã băm thành {len(chunks)} đoạn.\n")

    print("2. Đang khởi động não bộ (Vector DB)...")
    print("   (LƯU Ý: Lần chạy đầu tiên sẽ mất 1-2 phút để tải mô hình AI từ HuggingFace về máy)\n")
    db_manager = VectorDBManager()

    print("3. Đang ghi nhớ kiến thức vào Database...")
    db_manager.add_documents(chunks)
    print("   -> Đã lưu thành công vào thư mục 'chroma_db'!\n")

    print("4. TEST TRÍ NHỚ (TÌM KIẾM THEO NGỮ NGHĨA)")
    query = "Ngoài lập trình ra thì tác giả còn sở thích nào khác không?"
    print(f"   Câu hỏi: {query}")
    
    # Tìm kiếm 1 đoạn văn bản liên quan nhất
    results = db_manager.search(query, k=1)
    
    print("\n   Kết quả bộ nhớ trích xuất được:")
    for res in results:
        print(f"   => [{res.page_content}]")

finally:
    # Dọn dẹp file test sau khi chạy xong
    if os.path.exists(test_file):
        os.remove(test_file)