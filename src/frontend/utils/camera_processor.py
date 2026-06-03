import time
import threading
import traceback

import av
import cv2
import mediapipe as mp

try:
    from streamlit_webrtc import VideoProcessorBase
except ImportError:
    # Fallback cho version streamlit-webrtc cũ
    from streamlit_webrtc import VideoTransformerBase as VideoProcessorBase


class HandGestureProcessor(VideoProcessorBase):
    """
    Xử lý camera realtime cho Streamlit WebRTC.

    Nhiệm vụ:
    - Nhận frame từ browser.
    - Dùng MediaPipe detect bàn tay.
    - Đếm số ngón 1, 2, 3.
    - Nếu giữ ổn định trong 2 giây thì lưu confirmed_command.
    - dashboard.py sẽ đọc command này và map sang câu hỏi.

    Lưu ý:
    - Không gọi API backend trong recv().
    - recv() chạy liên tục theo frame, gọi API ở đây sẽ dễ lag/đơ camera.
    """

    def __init__(self):
        # Lazy init MediaPipe để tránh lỗi thread khi WebRTC chưa sẵn sàng
        self.hands_detector = None
        self.mp_hands = None
        self.mp_draw = None

        # Gesture state
        self.current_fingers = 0
        self.hold_start_time = 0.0
        self.hold_seconds = 2.0
        self.command_latched = False

        # Thread-safe command sharing với Streamlit main thread
        self._command_lock = threading.Lock()
        self.confirmed_command = None

        # Debug state
        self.last_error = None
        self.last_error_print_time = 0.0

    # =====================================================
    # PUBLIC METHOD: dashboard.py sẽ gọi hàm này
    # =====================================================
    def get_confirmed_command(self, clear: bool = True):
        """
        Lấy command đã chốt.
        clear=True để sau khi dashboard đọc xong thì xóa command,
        tránh bị xử lý lại ở lần rerun tiếp theo.
        """
        with self._command_lock:
            command = self.confirmed_command
            if clear:
                self.confirmed_command = None
            return command

    def _set_confirmed_command(self, command: int):
        with self._command_lock:
            self.confirmed_command = command

    # =====================================================
    # MEDIAPIPE INIT
    # =====================================================
    def _ensure_detector(self):
        if self.hands_detector is not None:
            return

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands_detector = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    # =====================================================
    # FINGER COUNT
    # =====================================================
    def _count_fingers(self, hand_landmarks) -> int:
        """
        Đếm 4 ngón chính: trỏ, giữa, áp út, út.
        Không đếm ngón cái để tránh sai do xoay tay trái/phải.

        Mapping UI:
        - 1 ngón -> câu hỏi 1
        - 2 ngón -> câu hỏi 2
        - 3 ngón -> câu hỏi 3
        """
        lm = hand_landmarks.landmark
        fingers = 0

        # Index finger
        if lm[8].y < lm[6].y:
            fingers += 1

        # Middle finger
        if lm[12].y < lm[10].y:
            fingers += 1

        # Ring finger
        if lm[16].y < lm[14].y:
            fingers += 1

        # Pinky finger
        if lm[20].y < lm[18].y:
            fingers += 1

        return fingers

    # =====================================================
    # MAIN VIDEO CALLBACK
    # =====================================================
    def recv(self, frame):
        try:
            self._ensure_detector()

            img = frame.to_ndarray(format="bgr24")
            img = cv2.flip(img, 1)

            # Giảm tải xử lý cho Railway.
            # Nếu browser đã gửi 320x240 thì dòng này gần như không ảnh hưởng.
            img = cv2.resize(img, (320, 240))

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False

            results = self.hands_detector.process(rgb)

            fingers = 0
            hand_detected = False

            if results.multi_hand_landmarks:
                hand_detected = True

                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                    )
                    fingers = self._count_fingers(hand_landmarks)

                    # Chỉ xử lý 1 bàn tay
                    break

            # =================================================
            # GESTURE CONFIRM LOGIC
            # =================================================
            if hand_detected and 1 <= fingers <= 3:
                if fingers != self.current_fingers:
                    self.current_fingers = fingers
                    self.hold_start_time = time.time()
                    self.command_latched = False
                else:
                    elapsed = time.time() - self.hold_start_time

                    if elapsed >= self.hold_seconds:
                        if not self.command_latched:
                            self._set_confirmed_command(fingers)
                            self.command_latched = True

                        cv2.putText(
                            img,
                            f"DA CHOT LENH: {fingers}",
                            (15, 105),
                            cv2.FONT_HERSHEY_DUPLEX,
                            0.75,
                            (0, 0, 255),
                            2,
                        )
                    else:
                        progress = int((elapsed / self.hold_seconds) * 100)
                        cv2.putText(
                            img,
                            f"Giu nguyen... {progress}%",
                            (15, 105),
                            cv2.FONT_HERSHEY_DUPLEX,
                            0.65,
                            (0, 255, 255),
                            2,
                        )

            else:
                # Không có tay hoặc số ngón không hợp lệ
                self.current_fingers = 0
                self.hold_start_time = 0.0
                self.command_latched = False

                if hand_detected and fingers > 3:
                    cv2.putText(
                        img,
                        "Chi ho tro 1-3 ngon",
                        (15, 105),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.65,
                        (0, 165, 255),
                        2,
                    )

            # =================================================
            # DEBUG OVERLAY
            # =================================================
            cv2.putText(
                img,
                f"So ngon tay: {fingers}",
                (15, 40),
                cv2.FONT_HERSHEY_DUPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            if not hand_detected:
                cv2.putText(
                    img,
                    "Khong thay ban tay",
                    (15, 70),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.55,
                    (180, 180, 180),
                    1,
                )

            return av.VideoFrame.from_ndarray(img, format="bgr24")

        except Exception as e:
            self.last_error = str(e)

            # In lỗi có kiểm soát để Railway log không bị spam mỗi frame
            now = time.time()
            if now - self.last_error_print_time > 2.0:
                print("[CameraProcessor Error]")
                traceback.print_exc()
                self.last_error_print_time = now

            # Trả frame gốc nếu xử lý lỗi để camera không chết hẳn
            img = frame.to_ndarray(format="bgr24")
            img = cv2.flip(img, 1)
            img = cv2.resize(img, (320, 240))

            cv2.putText(
                img,
                "Camera Processor Error",
                (15, 40),
                cv2.FONT_HERSHEY_DUPLEX,
                0.65,
                (0, 0, 255),
                2,
            )

            cv2.putText(
                img,
                str(e)[:35],
                (15, 70),
                cv2.FONT_HERSHEY_DUPLEX,
                0.45,
                (0, 0, 255),
                1,
            )

            return av.VideoFrame.from_ndarray(img, format="bgr24")