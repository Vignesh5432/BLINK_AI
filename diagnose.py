import sys
print("Python executable:", sys.executable)
print("Attempting imports...")
try:
    import cv2
    print("cv2 imported:", cv2.__version__)
    import mediapipe
    print("mediapipe imported")
    import numpy
    print("numpy imported")
    import pyttsx3
    print("pyttsx3 imported")
except ImportError as e:
    print("Import failed:", e)
    sys.exit(1)

print("Attempting to open camera...")
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("Camera opened successfully")
    cap.release()
else:
    print("Failed to open camera 0")
    # Try other indices
    for i in range(1, 4):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera opened successfully on index {i}")
            cap.release()
            break
        else:
            print(f"Failed to open camera {i}")

print("Diagnosis complete.")
