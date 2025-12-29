import cv2
import time
import mediapipe as mp
try:
    from mediapipe import solutions
    mp.solutions = solutions
except ImportError:
    try:
        import mediapipe.python.solutions as solutions
        mp.solutions = solutions
    except ImportError:
        pass
import numpy as np
from scipy.spatial import distance as dist
from config import BLINK_CONSEC_FRAMES

class BlinkEvent:
    def __init__(self, duration, end_time):
        self.duration = duration
        self.end_time = end_time

class BlinkDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Landmark indices for Left and Right eyes
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
        self.closing_start_time = None
        self.is_closed = False
        # We still use a small buffer to avoid noise (e.g. 50ms)
        self.MIN_BLINK_DURATION = 0.05 
        
    def calculate_ear(self, landmarks, indices):
        """Calculates Eye Aspect Ratio (EAR) for a set of eye landmarks."""
        A = dist.euclidean(landmarks[indices[1]], landmarks[indices[5]])
        B = dist.euclidean(landmarks[indices[2]], landmarks[indices[4]])
        C = dist.euclidean(landmarks[indices[0]], landmarks[indices[3]])

        if C == 0: 
            return 0.0

        ear = (A + B) / (2.0 * C)
        return ear

    def process_frame(self, frame, threshold):
        """
        Processes a video frame to detect face landmarks and calculate EAR.
        Returns: (left_ear, right_ear, landmarks_list, blink_event)
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        
        left_ear = 0.0
        right_ear = 0.0
        face_landmarks_np = []
        blink_event = None
        avg_ear = 0.0

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, c = frame.shape
                
                landmarks = [(int(pt.x * w), int(pt.y * h)) for pt in face_landmarks.landmark]
                face_landmarks_np = landmarks
                
                left_ear = self.calculate_ear(landmarks, self.LEFT_EYE)
                right_ear = self.calculate_ear(landmarks, self.RIGHT_EYE)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Check Blink State
                current_time = time.time()
                
                if avg_ear < threshold:
                    # Eye Closed
                    if not self.is_closed:
                        self.is_closed = True
                        self.closing_start_time = current_time
                else:
                    # Eye Open
                    if self.is_closed:
                        # Transition Closed -> Open
                        self.is_closed = False
                        if self.closing_start_time:
                            duration = current_time - self.closing_start_time
                            # Filter noise
                            if duration >= self.MIN_BLINK_DURATION:
                                blink_event = BlinkEvent(duration, current_time)
                        self.closing_start_time = None
                
                break
                
        return left_ear, right_ear, face_landmarks_np, blink_event

    def get_eye_coords(self, landmarks, indices):
        """Helper to get coordinates for drawing."""
        return [landmarks[i] for i in indices]
