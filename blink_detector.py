import cv2
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
        # Chosen based on standard MediaPipe FaceMesh topology
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]

    def calculate_ear(self, landmarks, indices):
        """Calculates Eye Aspect Ratio (EAR) for a set of eye landmarks."""
        # Vertical distances
        A = dist.euclidean(landmarks[indices[1]], landmarks[indices[5]])
        B = dist.euclidean(landmarks[indices[2]], landmarks[indices[4]])

        # Horizontal distance
        C = dist.euclidean(landmarks[indices[0]], landmarks[indices[3]])

        if C == 0: # Avoid division by zero
            return 0.0

        ear = (A + B) / (2.0 * C)
        return ear

    def process_frame(self, frame):
        """
        Processes a video frame to detect face landmarks and calculate EAR.
        Returns: (left_ear, right_ear, landmarks_list)
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        
        left_ear = 0.0
        right_ear = 0.0
        face_landmarks_np = []

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, c = frame.shape
                
                # Convert landmarks to pixel coordinates
                landmarks = [(int(pt.x * w), int(pt.y * h)) for pt in face_landmarks.landmark]
                face_landmarks_np = landmarks
                
                # Calculate EAR for both eyes
                left_ear = self.calculate_ear(landmarks, self.LEFT_EYE)
                right_ear = self.calculate_ear(landmarks, self.RIGHT_EYE)
                
                # We only process the first detected face
                break
                
        return left_ear, right_ear, face_landmarks_np

    def get_eye_coords(self, landmarks, indices):
        """Helper to get coordinates for drawing."""
        return [landmarks[i] for i in indices]
