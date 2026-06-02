import json
import os
import requests
from typing import Any, Dict, List, Optional

# BASE_URL được lấy từ biến môi trường, hoặc mặc định là localhost cho local testing
BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- 1. ĐĂNG NHẬP VÀ TẠO TÀI KHOẢN ---
def register_user(username: str) -> Optional[Dict[str, Any]]:
    """Đăng ký một người dùng mới với username cung cấp."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", json={"username": username}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during registration: {e}")
        return None

def login_user(username: str) -> Optional[Dict[str, Any]]:
    """Đăng nhập người dùng với username cung cấp."""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={"username": username})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during login: {e}")
        return None

# --- 2. QUẢN LÝ TÀI LIỆU --
def upload_document(token: str, file_path: str) -> Optional[Dict[str, Any]]:
    """Tải lên một tài liệu với token xác thực."""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(f"{BASE_URL}/documents", files=files, headers=headers)
            response.raise_for_status()
            return response.json()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error uploading document: {e}")
        return None

def get_documents(token: str) -> Optional[List[Dict[str, Any]]]:
    """Lấy danh sách các tài liệu đã tải lên."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/documents", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting documents: {e}")
        return None

# --- 3. CHAT VỚI MODEL ---
def chat_with_model(token: str, user_message: str, chat_history: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """Gửi tin nhắn người dùng và nhận phản hồi từ model."""
    try:
        payload = {
            "user_message": user_message,
            "chat_history": chat_history,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error chatting with model: {e}")
        return None

# --- 4. NHẬN CÂU HỎI TỪ MODEL ---
def get_questions_from_model(token: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Yêu cầu model tạo câu hỏi dựa trên tài liệu đã tải lên."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/documents/{document_id}/questions", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting questions from model: {e}")
        return None

# --- 7. GỬI CẤU HÌNH VÀ TÍN HIỆU CỬ CHỈ ---
def send_gesture_command(gesture_id: int, token: str):
    """Gửi tín hiệu cử chỉ tay về backend."""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "gesture_id": gesture_id
    }
    try:
        response = requests.post(
            f"{BASE_URL}/gestures/action", 
            json=payload, 
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error sending gesture command: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error sending gesture command: {e}")
        return None
