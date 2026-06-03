import time
import threading
import traceback

import av
import cv2
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_draw

try:
    from streamlit_webrtc import VideoProcessorBase
except ImportError:
    from streamlit_webrtc import VideoTransformerBase as VideoProcessorBase


class HandGestureProcessor(VideoProcessorBase):
    def __init__(self):
        self.hands_detector = None
        self.mp_hands = None
        self.mp_draw = None

        self.current_fingers = 0
        self.hold_start_time = 0.0
        self.hold_seconds = 2.0
        self.command_latched = False

        self._command_lock = threading.Lock()
        self.confirmed_command = None

        self.last_error = None
        self.last_error_print_time = 0.0

    def get_confirmed_command(self, clear: bool = True):
        with self._command_lock:
            command = self.confirmed_command
            if clear:
                self.confirmed_command = None
            return command

    def _set_confirmed_command(self, command: int):
        with self._command_lock:
            self.confirmed_command = command

    def _ensure_detector(self):
        if self.hands_detector is not None:
            return

        self.mp_hands = mp_hands
        self.mp_draw = mp_draw

        self.hands_detector = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def _count_fingers(self, hand_landmarks) -> int:
        lm = hand_landmarks.landmark
        fingers = 0

        if lm[8].y < lm[6].y:
            fingers += 1

        if lm[12].y < lm[10].y:
            fingers += 1

        if lm[16].y < lm[14].y:
            fingers += 1

        if lm[20].y < lm[18].y:
            fingers += 1

        return fingers

    def recv(self, frame):
        try:
            self._ensure_detector()

            img = frame.to_ndarray(format="bgr24")
            img = cv2.flip(img, 1)
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
                    break

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

            now = time.time()
            if now - self.last_error_print_time > 2.0:
                print("[CameraProcessor Error]")
                traceback.print_exc()
                self.last_error_print_time = now

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