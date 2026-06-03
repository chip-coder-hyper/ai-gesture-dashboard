import os

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from utils.api_client import (
    get_backend_base_url,
    send_chat_message,
    upload_file,
)
from utils.camera_processor import HandGestureProcessor


# =========================================================
# WEBRTC / TURN CONFIG
# =========================================================
def build_rtc_configuration():
    """
    Railway deploy cần STUN/TURN để WebRTC hoạt động ổn định.

    Set trên Railway frontend service:
        METERED_TURN_USERNAME=...
        METERED_TURN_CREDENTIAL=...

    Có thể dùng thêm:
        METERED_TURN_PASSWORD=...
    nếu bạn quen đặt tên là password.
    """
    username = os.getenv("METERED_TURN_USERNAME", "").strip()
    credential = (
        os.getenv("METERED_TURN_CREDENTIAL", "").strip()
        or os.getenv("METERED_TURN_PASSWORD", "").strip()
    )

    ice_servers = [
        {
            "urls": [
                "stun:stun.relay.metered.ca:80",
                "stun:stun.l.google.com:19302",
            ]
        }
    ]

    if username and credential:
        ice_servers.extend(
            [
                {
                    "urls": ["turn:global.relay.metered.ca:80"],
                    "username": username,
                    "credential": credential,
                },
                {
                    "urls": ["turn:global.relay.metered.ca:80?transport=tcp"],
                    "username": username,
                    "credential": credential,
                },
                {
                    "urls": ["turn:global.relay.metered.ca:443"],
                    "username": username,
                    "credential": credential,
                },
                {
                    "urls": ["turns:global.relay.metered.ca:443?transport=tcp"],
                    "username": username,
                    "credential": credential,
                },
            ]
        )

        return {
            "iceServers": ice_servers,
            "iceTransportPolicy": "relay",
        }

    return {
        "iceServers": ice_servers,
        "iceTransportPolicy": "all",
    }


def init_dashboard_state():
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "suggested_questions" not in st.session_state:
        st.session_state.suggested_questions = []

    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    if "last_gesture_command" not in st.session_state:
        st.session_state.last_gesture_command = None


# =========================================================
# MAIN DASHBOARD
# =========================================================
def render_main_dashboard():
    init_dashboard_state()

    token = st.session_state.get("token")

    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1000px !important;
                padding-top: 2rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("🤖 AI Workspace")

        if st.button(
            "💬 Phân tích Tài liệu",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "chat" else "secondary",
        ):
            st.session_state.current_page = "chat"
            st.rerun()

        if st.button(
            "🌟 NHẬN DIỆN CỬ CHỈ",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "camera" else "secondary",
        ):
            st.session_state.current_page = "camera"
            st.rerun()

        st.divider()

        if st.button("📝 Xóa phiên Chat", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.suggested_questions = []
            st.session_state.pending_question = None
            st.session_state.last_gesture_command = None
            st.rerun()

        with st.expander("⚙️ Debug"):
            st.caption("Backend URL frontend đang gọi:")
            st.code(get_backend_base_url())

            if os.getenv("METERED_TURN_USERNAME") and (
                os.getenv("METERED_TURN_CREDENTIAL") or os.getenv("METERED_TURN_PASSWORD")
            ):
                st.success("TURN credentials: OK")
            else:
                st.warning("TURN credentials: chưa set env")

    if not token:
        st.warning(
            "Chưa có token đăng nhập trong session_state. "
            "Hãy đăng nhập/guest login trước khi upload hoặc chat."
        )

    # =====================================================
    # PAGE: CHAT / DOCUMENT QA
    # =====================================================
    if st.session_state.current_page == "chat":
        render_chat_page(token)

    # =====================================================
    # PAGE: CAMERA
    # =====================================================
    elif st.session_state.current_page == "camera":
        render_camera_page()


# =========================================================
# CHAT PAGE
# =========================================================
def render_chat_page(token):
    if not st.session_state.session_id:
        st.header("Hệ thống Trợ lý Thông minh")
        st.caption("Upload tài liệu để AI sinh 3 câu hỏi gợi ý.")

        uploaded_file = st.file_uploader(
            "Nạp tài liệu PDF/Docx",
            type=["pdf", "docx"],
        )

        if uploaded_file:
            if not token:
                st.error("Bạn cần đăng nhập trước khi upload tài liệu.")
                return

            with st.spinner("AI đang đọc tri thức..."):
                result = upload_file(uploaded_file, token)

            if not result:
                st.error("Upload thất bại. Hãy kiểm tra Railway backend log.")
                return

            if result.get("status") == "success":
                st.session_state.session_id = result.get("session_id")
                st.session_state.suggested_questions = result.get(
                    "suggested_questions",
                    [],
                )
                st.session_state.messages = []
                st.session_state.pending_question = None
                st.success("Upload thành công!")
                st.rerun()

            else:
                st.error(result.get("message", "Upload thất bại!"))

        return

    st.header("💬 Chat với tài liệu")

    if st.session_state.suggested_questions:
        st.markdown("💡 **Câu hỏi gợi ý:**")
        cols = st.columns(min(len(st.session_state.suggested_questions), 3))

        for i, q in enumerate(st.session_state.suggested_questions[:3]):
            if cols[i].button(
                f"{i + 1}. {q}",
                use_container_width=True,
                key=f"suggested_question_{i}",
            ):
                st.session_state.pending_question = q
                st.rerun()

    chat_scroll_box = st.container(height=560, border=False)

    with chat_scroll_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    user_input = st.chat_input("Hỏi bất kỳ điều gì...")

    pending_question = st.session_state.get("pending_question")
    should_send = bool(user_input) or bool(pending_question)

    if should_send:
        q = user_input or pending_question
        st.session_state.pending_question = None

        if not token:
            st.error("Bạn cần đăng nhập trước khi chat.")
            return

        st.session_state.messages.append(
            {
                "role": "user",
                "content": q,
            }
        )

        with chat_scroll_box:
            with st.chat_message("user"):
                st.markdown(q)

            with st.chat_message("assistant"):
                with st.spinner("Đang phân tích..."):
                    res = send_chat_message(
                        message=q,
                        session_id=st.session_state.session_id,
                        token=token,
                    )

                    if not res:
                        reply = "Lỗi phản hồi từ backend. Hãy kiểm tra Railway log."
                    else:
                        reply = res.get("ai_response", "Lỗi phản hồi!")

                    st.markdown(reply)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        st.rerun()


# =========================================================
# CAMERA PAGE
# =========================================================
def render_camera_page():
    st.header("📷 Điều khiển AI bằng Cử chỉ")

    col_cam, col_info = st.columns([1.5, 1], gap="medium")

    with col_cam:
        rtc_configuration = build_rtc_configuration()

        webrtc_ctx = webrtc_streamer(
            key="gesture-camera",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=HandGestureProcessor,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 320},
                    "height": {"ideal": 240},
                    "frameRate": {"ideal": 10, "max": 15},
                },
                "audio": False,
            },
            video_html_attrs={
                "autoPlay": True,
                "controls": False,
                "playsInline": True,
                "muted": True,
            },
            sendback_audio=False,
            async_processing=True,
            desired_playing_state=True,
        )

        if webrtc_ctx.state.playing:
            st.success("Camera đang chạy. Hãy giơ 1–3 ngón tay và giữ 2 giây.")

            # Rerun nhẹ để main thread đọc command từ WebRTC thread.
            st_autorefresh(interval=1500, key="cam_refresh")

            processor = webrtc_ctx.video_processor

            if processor:
                if hasattr(processor, "get_confirmed_command"):
                    cmd = processor.get_confirmed_command(clear=True)
                else:
                    cmd = getattr(processor, "confirmed_command", None)
                    processor.confirmed_command = None

                if cmd:
                    handle_gesture_command(cmd)

                last_error = getattr(processor, "last_error", None)
                if last_error:
                    st.warning(f"Camera processor warning: {last_error}")

        else:
            st.info("Nhấn Start để bật camera.")

    with col_info:
        render_gesture_command_panel()


def handle_gesture_command(cmd: int):
    try:
        cmd = int(cmd)
    except Exception:
        st.warning("Tín hiệu cử chỉ không hợp lệ.")
        return

    st.session_state.last_gesture_command = cmd

    if not st.session_state.session_id:
        st.warning("Vui lòng tải tài liệu bên mục Chat trước!")
        return

    questions = st.session_state.get("suggested_questions", [])

    if 1 <= cmd <= len(questions):
        selected_question = questions[cmd - 1]

        st.session_state.pending_question = selected_question
        st.session_state.current_page = "chat"

        st.success(f"Đã chọn câu hỏi số {cmd}: {selected_question}")
        st.rerun()

    else:
        st.warning(f"Cử chỉ {cmd} chưa có câu hỏi tương ứng.")


def render_gesture_command_panel():
    st.subheader("Bảng Lệnh Cử Chỉ")

    if not st.session_state.session_id:
        st.info("Hãy tải tài liệu bên mục Chat để sinh bảng lệnh!")
        return

    questions = st.session_state.get("suggested_questions", [])

    if not questions:
        st.warning("Chưa có câu hỏi gợi ý.")
        return

    for i, q in enumerate(questions[:3]):
        st.markdown(
            f"""
            <div style="
                background-color: #1e293b;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                border-left: 4px solid #10b981;
            ">
                <h4 style="margin:0; color: #10b981;">{i + 1} Ngón tay</h4>
                <p style="margin: 5px 0 0 0; color: white;">{q}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    last_cmd = st.session_state.get("last_gesture_command")

    if last_cmd:
        st.caption(f"Lệnh gần nhất: {last_cmd} ngón tay")