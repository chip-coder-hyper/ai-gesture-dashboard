
import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=1, 
            min_detection_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def count_fingers(self):
        fingers = []
        if hasattr(self, 'results') and self.results.multi_hand_landmarks:
            hand_lms = self.results.multi_hand_landmarks[0].landmark
            
            if hand_lms[self.tip_ids[0]].x < hand_lms[self.tip_ids[0] - 1].x:
                fingers.append(1)
            else:
                fingers.append(0)
                
            for id in range(1, 5):
                if hand_lms[self.tip_ids[id]].y < hand_lms[self.tip_ids[id] - 2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)
                    
        return fingers.count(1) if fingers else 0