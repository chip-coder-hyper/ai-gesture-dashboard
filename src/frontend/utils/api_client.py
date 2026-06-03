import os
import requests
from typing import Any, Dict, List, Optional


BACKEND_HOST = os.getenv("BACKEND_URL", "http://127.0.0.1:8080").rstrip("/")

if BACKEND_HOST.endswith("/api/v1"):
    BASE_URL = BACKEND_HOST
else:
    BASE_URL = f"{BACKEND_HOST}/api/v1"


def _auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# =========================================================
# AUTH - DEMO SAFE
# =========================================================
def register_user(username: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
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


def login_user(username: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
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
# DOCUMENT UPLOAD
# =========================================================
def upload_file(uploaded_file, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
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


def upload_document(token: Optional[str], file_path: str) -> Optional[Dict[str, Any]]:
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
# CHAT
# =========================================================
def send_chat_message(
    message: str,
    session_id: int,
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
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
    token: Optional[str],
    user_message: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    if session_id is None:
        print("[API Chat Error] Missing session_id.")
        return None

    return send_chat_message(user_message, session_id, token)


# =========================================================
# SESSIONS
# =========================================================
def get_chat_sessions(token: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
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
    token: Optional[str] = None,
) -> Optional[List[Dict[str, Any]]]:
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


def get_documents(token: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    return get_chat_sessions(token)


def get_questions_from_model(
    token: Optional[str],
    document_id: str,
) -> Optional[Dict[str, Any]]:
    print("[API Warning] Suggested questions are returned by upload_file().")
    return None


# =========================================================
# OPTIONAL GESTURE API
# =========================================================
def send_gesture_command(
    gesture_id: int,
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
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


def get_backend_base_url() -> str:
    return BASE_URL