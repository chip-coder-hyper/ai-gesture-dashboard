from abc import ABC, abstractmethod
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Strategy Pattern: Tạo bản thiết kế chung cho mọi loại AI
class BaseLLMProvider(ABC):
    @abstractmethod
    def get_model(self):
        pass

# 2. Lớp cụ thể xử lý Google Gemini
class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Sử dụng siêu AI thế hệ mới!
            google_api_key=api_key,
            temperature=0.2,
            max_retries=2
        )

    def get_model(self):
        return self.llm

# 3. Factory Pattern: Nhà máy điều phối mô hình AI
class LLMFactory:
    @staticmethod
    def get_llm(provider_name: str, api_key: str):
        if provider_name.lower() == "gemini":
            return GeminiProvider(api_key).get_model()
        else:
            raise ValueError(f"Hệ thống chưa hỗ trợ mô hình AI: {provider_name}")