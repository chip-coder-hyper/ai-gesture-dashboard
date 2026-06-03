import os
import requests
from typing import Any, Dict, List, Optional


# =========================================================
# BACKEND URL CONFIG
# =========================================================
# Railway nên set:
# BACKEND_URL=https://your-backend-service.up.railway.app
#
# Không cần tự thêm /api/v1 trong Railway env.
# File này sẽ tự nối /api/v1 để tránh sai endpoint.
# Local backend của bạn đang chạy port 8080 trong main.py.
BACKEND_HOST = os.getenv("BACKEND_URL", "http://127.0.0.1:8080").rstrip("/")

if BACKEND_HOST.endswith("/api/v1"):
    BASE_URL = BACKEND_HOST
else:
    BASE_URL = f"{BACKEND_HOST}/api/v1"


def _auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _safe_json(response: requests.Response) -> Dict[str, Any]:
    try:
        return response.json()
    except Exception:
        return {
            "status": "error",
            "message": response.text,
        }


# =========================================================
# 1. AUTH
# =========================================================
def register_user(username: str) -> Optional[Dict[str, Any]]:
    """Đăng ký user mới."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": username},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[API Register Error] {e}")
        return None


def login_user(username: str) -> Optional[Dict[str, Any]]:
    """Đăng nhập user."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[API Login Error] {e}")
        return None


# =========================================================
# 2. DOCUMENT UPLOAD
# =========================================================
def upload_file(uploaded_file, token: str) -> Optional[Dict[str, Any]]:
    """
    Upload file từ Streamlit file_uploader lên backend.

    Backend thật:
        POST /api/v1/documents/upload
    """
    if uploaded_file is None:
        return None

    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        }

        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            headers=_auth_headers(token),
            timeout=180,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[API Upload Error] {e}")
        return None


def upload_document(token: str, file_path: str) -> Optional[Dict[str, Any]]:
    """
    Upload file từ đường dẫn local.
    Giữ lại để tương thích với code cũ nếu còn nơi nào gọi upload_document().
    """
    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (
                    os.path.basename(file_path),
                    f,
                    "application/octet-stream",
                )
            }

            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                headers=_auth_headers(token),
                timeout=180,
            )

            response.raise_for_status()
            return response.json()

    except FileNotFoundError:
        print(f"[API Upload Error] File not found: {file_path}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[API Upload Error] {e}")
        return None


# =========================================================
# 3. CHAT / RAG
# =========================================================
def send_chat_message(
    message: str,
    session_id: int,
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Gửi câu hỏi tới RAG backend.

    Backend thật:
        POST /api/v1/documents/chat

    Payload backend yêu cầu:
        {
            "session_id": int,
            "query": str
        }
    """
    try:
        payload = {
            "session_id": int(session_id),
            "query": message,
        }

        response = requests.post(
            f"{BASE_URL}/documents/chat",
            json=payload,
            headers=_auth_headers(token),
            timeout=180,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[API Chat Error] {e}")
        return None
    except Exception as e:
        print(f"[API Chat Unexpected Error] {e}")
        return None


def chat_with_model(
    token: str,
    user_message: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Wrapper giữ tương thích với code cũ.

    Nếu code cũ gọi chat_with_model mà không truyền session_id
    thì backend hiện tại không thể xử lý vì document_api.py yêu cầu session_id.
    """
    if session_id is None:
        print("[API Chat Error] Missing session_id for chat_with_model().")
        return None

    return send_chat_message(user_message, session_id, token)


# =========================================================
# 4. CHAT SESSIONS
# =========================================================
def get_chat_sessions(token: str) -> Optional[List[Dict[str, Any]]]:
    """
    Lấy danh sách phiên chat cũ.

    Backend thật:
        GET /api/v1/documents/sessions
    """
    try:
        response = requests.get(
            f"{BASE_URL}/documents/sessions",
            headers=_auth_headers(token),
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[API Sessions Error] {e}")
        return None


def get_session_messages(
    session_id: int,
    token: str,
) -> Optional[List[Dict[str, Any]]]:
    """
    Lấy tin nhắn của một session.

    Backend thật:
        GET /api/v1/documents/sessions/{session_id}/messages
    """
    try:
        response = requests.get(
            f"{BASE_URL}/documents/sessions/{int(session_id)}/messages",
            headers=_auth_headers(token),
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[API Messages Error] {e}")
        return None


def get_documents(token: str) -> Optional[List[Dict[str, Any]]]:
    """
    Alias tương thích code cũ.
    Hiện backend không có GET /documents, nên map sang sessions.
    """
    return get_chat_sessions(token)


# =========================================================
# 5. SUGGESTED QUESTIONS
# =========================================================
def get_questions_from_model(
    token: str,
    document_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Backend hiện tại KHÔNG có endpoint:
        GET /api/v1/documents/{document_id}/questions

    Suggested questions được trả về trực tiếp sau upload.
    Giữ hàm này để tránh crash nếu code cũ còn import.
    """
    print(
        "[API Warning] get_questions_from_model() is deprecated. "
        "Suggested questions are returned by upload_file()."
    )
    return None


# =========================================================
# 6. OPTIONAL GESTURE API
# =========================================================
def send_gesture_command(
    gesture_id: int,
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    API gesture hiện tại tồn tại ở:
        POST /api/v1/gestures/action

    Tuy nhiên flow chính của dashboard KHÔNG cần gọi hàm này.
    Camera chỉ cần set confirmed_command, dashboard sẽ map sang câu hỏi.
    Hàm này giữ lại để test Swagger/API nếu cần.
    """
    try:
        payload = {
            "gesture_id": int(gesture_id),
        }

        response = requests.post(
            f"{BASE_URL}/gestures/action",
            json=payload,
            headers=_auth_headers(token),
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[API Gesture Error] {e}")
        return None


# =========================================================
# 7. DEBUG HELPER
# =========================================================
def get_backend_base_url() -> str:
    """Dùng để debug xem frontend đang gọi backend nào."""
    return BASE_URL