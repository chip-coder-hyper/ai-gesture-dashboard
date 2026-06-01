from services.vector_db import VectorDBManager
from services.llm_factory import LLMFactory
from core.config import settings

class RAGEngine:
    def __init__(self):
        # Khởi tạo Trí nhớ (Vector DB) và Trí tuệ (Gemini 2.5 Flash)
        self.db_manager = VectorDBManager()
        self.llm = LLMFactory.get_llm("gemini", settings.GEMINI_API_KEY)

    def get_context(self, query: str, k: int = 3):
        """Lục tìm k đoạn văn bản sát nghĩa nhất với câu hỏi"""
        results = self.db_manager.search(query, k=k)
        # Nối các đoạn văn bản lại với nhau
        context = "\n".join([res.page_content for res in results])
        return context

    def generate_quiz(self):
        """Option 1: Chế độ sinh câu hỏi trắc nghiệm RAG"""
        context = self.get_context("tóm tắt các định nghĩa và ý chính quan trọng", k=2)
        
        prompt = f"""Dựa vào nội dung tài liệu sau đây:
        {context}
        
        Hãy tạo ra 1 câu hỏi trắc nghiệm để kiểm tra người đọc. 
        Bao gồm 4 đáp án được đánh số 1, 2, 3, 4. 
        Chỉ định rõ đáp án nào là đúng và giải thích ngắn gọn tại sao.
        """
        response = self.llm.invoke(prompt)
        return response.content

    def execute_gesture_command(self, gesture_id: int):
        """Option 2: Chế độ nhận diện cử chỉ tay (MediaPipe) để ra lệnh"""
        # Từ điển map số ngón tay với lệnh điều khiển AI
        commands = {
            1: "Hãy tóm tắt 3 ý chính của tài liệu này một cách ngắn gọn nhất.",
            2: "Liệt kê các từ khóa chuyên ngành hoặc khái niệm quan trọng nhất trong tài liệu.",
            5: "Hãy giải thích ngắn gọn mục đích chính của tài liệu này cho một người mới bắt đầu."
        }
        
        if gesture_id not in commands:
            return "Cử chỉ không hợp lệ. Hãy giơ 1 ngón, 2 ngón hoặc xòe 5 ngón tay."

        user_query = commands[gesture_id]
        context = self.get_context(user_query, k=3)

        prompt = f"""Bạn là một trợ lý AI thông minh. Dựa vào thông tin được cung cấp dưới đây:
        {context}

        Hãy thực hiện yêu cầu sau của người dùng: {user_query}
        Trả lời bằng tiếng Việt, ngắn gọn, súc tích và dễ hiểu.
        """
        response = self.llm.invoke(prompt)
        return response.content