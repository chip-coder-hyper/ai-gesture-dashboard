import cv2
import av
import time
# Import đích danh để tránh lỗi AttributeError trên server
from mediapipe.python.solutions import hands, drawing_utils
from streamlit_webrtc import VideoTransformerBase

class HandGestureProcessor(VideoTransformerBase):
    def __init__(self):
        # KHÔNG khởi tạo MediaPipe ở đây, luồng chính và luồng Camera sẽ đá nhau
        self.hands_detector = None
        self.current_fingers = 0
        self.hold_start_time = 0
        self.confirmed_command = None

    def recv(self, frame):
        # Chỉ khởi tạo khi luồng Camera thực sự đã mở (Lazy Init)
        if self.hands_detector is None:
            self.hands_detector = hands.Hands(
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
            results = self.hands_detector.process(rgb)
            fingers = 0
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    drawing_utils.draw_landmarks(img, hand_landmarks, hands.HAND_CONNECTIONS)
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