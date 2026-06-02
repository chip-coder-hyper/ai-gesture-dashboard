import cv2
import av
import time
import mediapipe as mp # Quay lại cách gọi chuẩn của MediaPipe
from streamlit_webrtc import VideoTransformerBase

class HandGestureProcessor(VideoTransformerBase):
    def __init__(self):
        # KHAI BÁO RỖNG: Tuyệt đối chưa gọi mp.solutions ở đây để tránh lỗi luồng (AttributeError)
        self.hands_detector = None
        self.mp_hands = None
        self.mp_draw = None
        
        self.current_fingers = 0
        self.hold_start_time = 0
        self.confirmed_command = None

    def recv(self, frame):
        # LAZY INIT: Chỉ gọi và khởi tạo MediaPipe khi luồng Camera thực sự đã bật
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
        
        try:
            print('[DEBUG] Hàm recv được gọi')
            results = self.hands_detector.process(rgb)
            fingers = 0
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    lm = hand_landmarks.landmark
                    if lm[8].y < lm[6].y: fingers += 1   
                    if lm[12].y < lm[10].y: fingers += 1 
                    if lm[16].y < lm[14].y: fingers += 1 
                    if lm[20].y < lm[18].y: fingers += 1 

            # Thêm trạng thái khoá sau khi chốt lệnh
            if self.confirmed_command is not None:
                if fingers == 0:
                    # Nếu tay đã bỏ ra, reset trạng thái để nhận lệnh mới
                    print(f"[DEBUG] Reset được trạng thái confirm lệnh: {self.confirmed_command}")
                    self.confirmed_command = None
                    self.current_fingers = 0
                    self.hold_start_time = 0
                else:
                    # Đã khóa, chỉ hiển thị trạng thái đã chốt lệnh
                    cv2.putText(img, "DA CHOT LENH!", (20, 120), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)
                    cv2.putText(img, f"So ngon tay: {self.confirmed_command}", (20, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 0), 3)
                    return av.VideoFrame.from_ndarray(img, format="bgr24")

            if fingers > 0:
                if fingers == self.current_fingers:
                    if self.hold_start_time == 0:
                        self.hold_start_time = time.time()
                    elapsed = time.time() - self.hold_start_time
                    if elapsed >= 2.0:
                        if self.confirmed_command is None:
                            print(f"[DEBUG] Đã chốt lệnh: {fingers}")
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
        except Exception as e:
            print(f"[ERROR][camera_processor.py]: {e}")

        return av.VideoFrame.from_ndarray(img, format="bgr24")