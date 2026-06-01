import streamlit as st
import cv2
import mediapipe as mp
import av
import time
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from streamlit_autorefresh import st_autorefresh

from utils.api_client import upload_file, send_chat_message, get_chat_sessions, get_session_messages

# ==========================================
# LÕI XỬ LÝ CAMERA 
# ==========================================
class HandGestureProcessor(VideoTransformerBase):
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1, 
            model_complexity=0, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.current_fingers = 0
        self.hold_start_time = 0
        self.confirmed_command = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1) 
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        try:
            results = self.hands.process(rgb)
            fingers = 0
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    lm = hand_landmarks.landmark
                    if lm[8].y < lm[6].y: fingers += 1   
                    if lm[12].y < lm[10].y: fingers += 1 
                    if lm[16].y < lm[14].y: fingers += 1 
                    if lm[20].y < lm[18].y: fingers += 1 

            if fingers > 0:
                if fingers == self.current_fingers:
                    if self.hold_start_time == 0:
                        self.hold_start_time = time.time()
                        
                    elapsed = time.time() - self.hold_start_time
                    if elapsed >= 2.0:
                        self.confirmed_command = fingers
                        cv2.putText(img, "DA CHOT LENH!", (20, 120), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)
                    else:
                        progress = int((elapsed / 2.0) * 100)
                        cv2.putText(img, f"Giu nguyen... {progress}%", (20, 120), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 255), 2)
                else:
                    self.current_fingers = fingers
                    self.hold_start_time = time.time()
            else:
                self.current_fingers = 0
                self.hold_start_time = 0

            cv2.putText(img, f"So ngon tay: {fingers}", (20, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 0), 3)
        except Exception:
            pass 

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
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

        # TẠO KHUNG CUỘN (SCROLL) TÀNG HÌNH CHO ĐOẠN CHAT
        # border=False giúp xóa bỏ cái khung vuông vức xấu xí!
        chat_scroll_box = st.container(height=600, border=False)

        # Mọi tin nhắn sẽ được nhét vào trong cái hộp cuộn này
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

        # Ô nhập liệu tự ghim xuống đáy màn hình
        user_input = st.chat_input("Hỏi bất kỳ điều gì...")
        
        if user_input or st.session_state.pending_question:
            q = user_input or st.session_state.pending_question
            st.session_state.pending_question = None
            
            st.session_state.messages.append({"role": "user", "content": q})
            
            # Đẩy tin nhắn mới vào thẳng trong hộp cuộn
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
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}, {"urls": ["stun:stun1.l.google.com:19302"]}]},
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