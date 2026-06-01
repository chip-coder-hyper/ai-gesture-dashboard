import streamlit as st
from streamlit_webrtc import webrtc_streamer
from streamlit_autorefresh import st_autorefresh

from utils.api_client import upload_file, send_chat_message
# Import Class xử lý camera đã được tách luồng an toàn
from utils.camera_processor import HandGestureProcessor

def render_main_dashboard():
    if "current_page" not in st.session_state: 
        st.session_state.current_page = "chat"

    st.markdown("<style>.block-container {max-width: 1000px !important; padding-top: 2rem !important;}</style>", unsafe_allow_html=True)

    with st.sidebar:
        st.title("🤖 AI Workspace")
        if st.button("💬 Phân tích Tài liệu", use_container_width=True, type="primary" if st.session_state.current_page == "chat" else "secondary"):
            st.session_state.current_page = "chat"; st.rerun()
            
        if st.button("🌟 NHẬN DIỆN CỬ CHỈ", use_container_width=True, type="primary" if st.session_state.current_page == "camera" else "secondary"):
            st.session_state.current_page = "camera"; st.rerun()
            
        st.divider()
        if st.button("📝 Xóa phiên Chat", use_container_width=True):
            st.session_state.session_id = None; st.session_state.messages = []; st.session_state.suggested_questions = []; st.rerun()

    # ==================== TRANG CHAT ====================
    if st.session_state.current_page == "chat":
        if not st.session_state.session_id:
            st.header("Hệ thống Trợ lý Thông minh")
            uploaded_file = st.file_uploader("Nạp tài liệu PDF/Docx", type=["pdf", "docx"])
            if uploaded_file:
                with st.spinner("AI đang đọc tri thức..."):
                    result = upload_file(uploaded_file, st.session_state.token)
                    if result.get("status") == "success":
                        st.session_state.session_id = result["session_id"]
                        st.session_state.suggested_questions = result.get("suggested_questions", [])
                        st.rerun()
            return 

        chat_scroll_box = st.container(height=600, border=False)

        with chat_scroll_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): 
                    st.markdown(msg["content"])
            
            if not st.session_state.messages and st.session_state.suggested_questions:
                st.markdown("<br>💡 **Câu hỏi gợi ý:**", unsafe_allow_html=True)
                cols = st.columns(min(len(st.session_state.suggested_questions), 3))
                for i, q in enumerate(st.session_state.suggested_questions[:3]):
                    if cols[i].button(q, use_container_width=True):
                        st.session_state.pending_question = q
                        st.rerun()

        user_input = st.chat_input("Hỏi bất kỳ điều gì...")
        
        if user_input or st.session_state.pending_question:
            q = user_input or st.session_state.pending_question
            st.session_state.pending_question = None
            
            st.session_state.messages.append({"role": "user", "content": q})
            
            with chat_scroll_box:
                with st.chat_message("user"): 
                    st.markdown(q)
                    
                with st.chat_message("assistant"):
                    with st.spinner("Đang phân tích..."):
                        res = send_chat_message(q, st.session_state.session_id, st.session_state.token)
                        reply = res.get("ai_response", "Lỗi phản hồi!")
                        st.markdown(reply)
                        
            st.session_state.messages.append({"role": "assistant", "content": reply})

    # ==================== TRANG CAMERA ====================
    elif st.session_state.current_page == "camera":
        st.header("📷 Điều khiển AI bằng Cử chỉ")
        col_cam, col_info = st.columns([1.5, 1], gap="medium")
        
        with col_cam:
            webrtc_ctx = webrtc_streamer(
                key="gesture-camera",
                video_processor_factory=HandGestureProcessor,
                rtc_configuration={
                    "iceServers": [
                        {"urls": ["stun:stun.l.google.com:19302"]}
                    ]
                },
                media_stream_constraints={"video": True, "audio": False},
                video_html_attrs={
                    "autoPlay": True, 
                    "controls": False, 
                    "playsInline": True
                },
                # BÙA CHÚ CỨU MẠNG: Buộc nó truyền qua luồng chính của Streamlit
                sendback_audio=False,
                async_processing=True
            )
            
            if webrtc_ctx.state.playing:
                st_autorefresh(interval=1000, key="cam_refresh")
                
                if webrtc_ctx.video_processor and hasattr(webrtc_ctx.video_processor, "confirmed_command"):
                    cmd = webrtc_ctx.video_processor.confirmed_command
                    if cmd:
                        webrtc_ctx.video_processor.confirmed_command = None 
                        if not st.session_state.session_id:
                            st.warning("Vui lòng tải file bên mục Chat trước!")
                        elif 1 <= cmd <= len(st.session_state.suggested_questions):
                            st.session_state.pending_question = st.session_state.suggested_questions[cmd - 1]
                            st.session_state.current_page = "chat"
                            st.rerun()

        with col_info:
            st.subheader("Bảng Lệnh Cử Chỉ")
            if not st.session_state.session_id:
                st.info("Hãy tải tài liệu bên mục Chat để sinh bảng lệnh!")
            else:
                for i, q in enumerate(st.session_state.suggested_questions):
                    st.markdown(f'''
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #10b981;">
                        <h4 style="margin:0; color: #10b981;">{i+1} Ngón tay</h4>
                        <p style="margin: 5px 0 0 0; color: white;">{q}</p>
                    </div>
                    ''', unsafe_allow_html=True)