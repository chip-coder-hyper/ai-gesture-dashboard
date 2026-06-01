import streamlit as st
from utils.api_client import register_user, login_user
from streamlit_local_storage import LocalStorage

def render_auth_page():
    localS = LocalStorage()
    
    if "auth_mode" not in st.session_state: 
        st.session_state.auth_mode = "login"
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.title("Chào mừng trở lại")

        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                email = st.text_input("Địa chỉ email")
                password = st.text_input("Mật khẩu", type="password")
                if st.form_submit_button("Đăng nhập", use_container_width=True):
                    with st.spinner("Đang xác thực..."):
                        res = login_user(email, password)
                        if res.status_code == 200:
                            token = res.json()["access_token"]
                            localS.setItem("auth_token", token, key="set_token")
                            localS.setItem("user_email", email, key="set_email")
                            st.session_state.token = token
                            st.session_state.user_email = email
                            st.rerun()
                        else: 
                            st.error("Sai tài khoản hoặc mật khẩu!")
            
            if st.button("Chưa có tài khoản? Đăng ký", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
        else:
            with st.form("reg_form"):
                new_email = st.text_input("Email mới")
                new_pw = st.text_input("Mật khẩu", type="password")
                if st.form_submit_button("Đăng ký tài khoản", use_container_width=True):
                    if register_user(new_email, new_pw).status_code == 200: 
                        st.success("Thành công! Hãy đăng nhập.")
                        st.session_state.auth_mode = "login"
                    else: 
                        st.error("Lỗi đăng ký!")
            if st.button("Đã có tài khoản? Đăng nhập", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()