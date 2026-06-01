import os
import requests

# Lấy biến môi trường từ server, nếu không có thì mặc định dùng localhost
API_BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")

# Không được có dấu "/" ở cuối cùng của BACKEND_URL
BASE_URL = f"{API_BASE_URL}/api/v1"

# --- 1. GỌI API ĐĂNG KÝ ---
def register_user(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/register", 
        json={"email": email, "password": password}
    )
    return response

# --- 2. GỌI API ĐĂNG NHẬP ---
def login_user(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/login", 
        json={"email": email, "password": password}
    )
    return response

# --- 3. GỌI API NẠP TÀI LIỆU (Có trình vé Token) ---
def upload_file(file_obj, token):
    headers = {
        "Authorization": f"Bearer {token}"  # Kẹp vé vào header
    }
    files = {"file": (file_obj.name, file_obj, "application/pdf")}
    
    response = requests.post(
        f"{BASE_URL}/documents/upload", 
        files=files, 
        headers=headers
    )
    return response.json()

# --- 4. GỌI API CHAT (Có trình vé Token + Nhắc mã Session_ID) ---
def send_chat_message(message, session_id, token):
    headers = {
        "Authorization": f"Bearer {token}"  # Kẹp vé vào header
    }
    payload = {
        "query": message,
        "session_id": session_id  # Báo cho Backend biết đang chat ở luồng nào
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/chat", 
        json=payload, 
        headers=headers
    )
    return response.json()

# --- 5. LẤY DANH SÁCH SESSION CŨ ---
def get_chat_sessions(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/documents/sessions", headers=headers)
    return response.json() if response.status_code == 200 else []

# --- 6. LẤY LỊCH SỬ TIN NHẮN CỦA 1 SESSION ---
def get_session_messages(session_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/documents/sessions/{session_id}/messages", headers=headers)
    return response.json() if response.status_code == 200 else []