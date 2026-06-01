import streamlit as st
import uuid
from utils.api_client import register_user, login_user
from views.dashboard import render_main_dashboard

st.set_page_config(page_title="AI Workspace", page_icon="🤖", layout="wide")

# KHỞI TẠO BIẾN TRẠNG THÁI
if "token" not in st.session_state: st.session_state.token = None
if "user_email" not in st.session_state: st.session_state.user_email = None
if "session_id" not in st.session_state: st.session_state.session_id = None
if "messages" not in st.session_state: st.session_state.messages = []
if "suggested_questions" not in st.session_state: st.session_state.suggested_questions = []
if "pending_question" not in st.session_state: st.session_state.pending_question = None

if not st.session_state.token:
    with st.spinner("Đang kết nối và khởi tạo không gian trải nghiệm..."):
        # 1. Tạo một thông tin tài khoản Khách ngẫu nhiên
        random_id = uuid.uuid4().hex[:6]
        guest_email = f"guest_{random_id}@demo.com"
        guest_password = "demo_password_123"
        
        try:
            # 2. Gọi API thật để Đăng ký và Đăng nhập
            register_user(guest_email, guest_password)
            res = login_user(guest_email, guest_password)
            
            # 3. Lấy Token THẬT để đưa cho Dashboard
            if res.status_code == 200:
                st.session_state.token = res.json()["access_token"]
                st.session_state.user_email = "Nhà Tuyển Dụng"
                st.rerun()
            else:
                st.error("Backend từ chối đăng nhập. Hãy kiểm tra lại API!")
        except Exception as e:
            st.error(f"Không thể gọi API Backend: {e}")
else:
    render_main_dashboard()