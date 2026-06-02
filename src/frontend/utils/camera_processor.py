import cv2
import av
import time
import mediapipe as mp
from streamlit_webrtc import VideoTransformerBase
from utils.api_client import send_gesture_command


class HandGestureProcessor(VideoTransformerBase):
    def __init__(self, token):
        # Lưu token để gửi lệnh về backend
        self.token = token

        # LAZY INIT: Chưa khởi tạo MediaPipe ngay để tránh lỗi luồng camera
        self.hands_detector = None
        self.mp_hands = None
        self.mp_draw = None

        # Biến xử lý cử chỉ
        self.current_fingers = 0
        self.last_fingers = None
        self.hold_start_time = 0
        self.confirmed_command = None

        # Đếm số lệnh đã gửi
        self.commands_sent_count = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Khởi tạo MediaPipe khi camera bắt đầu chạy
        if self.hands_detector is None:
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils

            self.hands_detector = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        fingers = 0

        try:
            results = self.hands_detector.process(rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )

                    lm = hand_landmarks.landmark

                    # Đếm 4 ngón: trỏ, giữa, áp út, út
                    # Không tính ngón cái để giảm sai số
                    if lm[8].y < lm[6].y:
                        fingers += 1

                    if lm[12].y < lm[10].y:
                        fingers += 1

                    if lm[16].y < lm[14].y:
                        fingers += 1

                    if lm[20].y < lm[18].y:
                        fingers += 1

            # ==============================
            # LOGIC GIỮ CỬ CHỈ 2 GIÂY
            # ==============================
            if fingers > 0:
                if fingers == self.last_fingers:
                    if self.hold_start_time == 0:
                        self.hold_start_time = time.time()

                    elapsed = time.time() - self.hold_start_time

                    if elapsed >= 2.0:
                        # Chỉ gửi nếu cử chỉ này chưa được xác nhận
                        if self.confirmed_command != fingers:
                            self.confirmed_command = fingers

                            try:
                                send_gesture_command(int(fingers), self.token)
                                self.commands_sent_count += 1

                                print(
                                    f"Lệnh cử chỉ {int(fingers)} đã được gửi. "
                                    f"Tổng số lệnh: {self.commands_sent_count}"
                                )

                            except Exception as e:
                                print(f"Lỗi khi gửi lệnh cử chỉ: {e}")

                        cv2.putText(
                            img,
                            f"DA GUI LENH: {fingers}",
                            (20, 120),
                            cv2.FONT_HERSHEY_DUPLEX,
                            1.2,
                            (0, 0, 255),
                            3
                        )

                    else:
                        progress = int((elapsed / 2.0) * 100)

                        cv2.putText(
                            img,
                            f"Giu nguyen... {progress}%",
                            (20, 120),
                            cv2.FONT_HERSHEY_DUPLEX,
                            1.0,
                            (0, 255, 255),
                            2
                        )

                else:
                    # Cử chỉ thay đổi, bắt đầu đếm lại
                    self.last_fingers = fingers
                    self.current_fingers = fingers
                    self.hold_start_time = time.time()
                    self.confirmed_command = None

            else:
                # Không phát hiện ngón tay, reset trạng thái
                self.current_fingers = 0
                self.last_fingers = None
                self.hold_start_time = 0
                self.confirmed_command = None

            cv2.putText(
                img,
                f"So ngon tay: {fingers}",
                (20, 60),
                cv2.FONT_HERSHEY_DUPLEX,
                1.5,
                (0, 255, 0),
                3
            )

            cv2.putText(
                img,
                f"Lenh da gui: {self.commands_sent_count}",
                (20, 180),
                cv2.FONT_HERSHEY_DUPLEX,
                0.9,
                (255, 255, 255),
                2
            )

        except Exception as e:
            print(f"Lỗi xử lý camera: {e}")

        return av.VideoFrame.from_ndarray(img, format="bgr24")