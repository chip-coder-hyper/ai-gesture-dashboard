import os
from dotenv import load_dotenv

# Tự động tìm và nạp các biến từ file .env vào hệ điều hành
load_dotenv()

class Settings:
    _instance = None

    # Hàm __new__ đảm bảo class Settings này chỉ được khởi tạo đúng 1 lần duy nhất trong toàn bộ dự án (Singleton Pattern)
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            
            # Kéo API Key từ hệ điều hành ra
            cls._instance.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            
            # Chặn ngay từ vòng gửi xe nếu quên cấu hình Key
            if not cls._instance.GEMINI_API_KEY:
                raise ValueError("LỖI CẢNH BÁO: Không tìm thấy GEMINI_API_KEY trong file .env!")
                
        return cls._instance

# Khởi tạo một biến toàn cục duy nhất
settings = Settings()