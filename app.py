import cv2
import time
import numpy as np
from config import (
    EAR_THRESHOLD_DEFAULT, BLINK_CONSEC_FRAMES, 
    DOT_DURATION_THRESHOLD, LETTER_PAUSE_THRESHOLD, 
    WORD_PAUSE_THRESHOLD, CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT,
    CALIBRATION_DURATION
)
from blink_detector import BlinkDetector
from morse_logic import MorseDecoder
from tts_engine import TTSEngine

def draw_ui(frame, state, debug_info, decoder_data):
    """
    Draws the UI overlays on the frame.
    state: 'CALIBRATION' or 'ACTIVE'
    """
    h, w, _ = frame.shape
    
    # Bottom Panel for Text
    cv2.rectangle(frame, (0, h - 100), (w, h), (30, 30, 30), -1)
    
    if state == 'CALIBRATION':
        # Top banner
        cv2.rectangle(frame, (0, 0), (w, 60), (0, 100, 255), -1)
        cv2.putText(frame, "CALIBRATION MODE", (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Instructions
        time_left = debug_info.get('time_left', 0)
        cv2.putText(frame, "Blink naturally...", (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Time remaining: {time_left:.1f}s", (20, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
                   
    elif state == 'ACTIVE':
        # Top Status Bar
        cv2.rectangle(frame, (0, 0), (w, 40), (50, 50, 50), -1)
        
        # EAR and Threshold info
        ear = debug_info.get('ear', 0.0)
        thresh = debug_info.get('threshold', EAR_THRESHOLD_DEFAULT)
        cv2.putText(frame, f"EAR: {ear:.2f} | Thresh: {thresh:.2f}", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Blink Status
        if debug_info.get('blinking', False):
            cv2.circle(frame, (w - 30, 20), 10, (0, 0, 255), -1) # Red dot for blink
        else:
             cv2.circle(frame, (w - 30, 20), 10, (0, 255, 0), -1) # Green dot for open
             
        # Decoding Info
        # Current Signal
        signal = decoder_data.get('current_signals', '')
        cv2.putText(frame, f"Signal:: {signal}", (10, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                   
        # Current Word
        curr_word = decoder_data.get('current_word', '')
        cv2.putText(frame, f"Building: {curr_word}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 100), 2)
        
        # Full Sentence (in bottom panel)
        sentence = decoder_data.get('sentence', '')
        # Simple text wrapping or scrolling
        display_text = sentence[-50:] # Show last 50 chars
        cv2.putText(frame, display_text, (10, h - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

def main():
    detector = BlinkDetector()
    decoder = MorseDecoder()
    tts = TTSEngine()
    
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Calibration State
    calibration_active = True
    calibration_start_time = time.time()
    calibration_ears = []
    
    # Operational Constants (will be updated after calibration)
    current_ear_threshold = EAR_THRESHOLD_DEFAULT
    
    # Runtime State
    blink_start_time = 0
    blinking = False
    last_blink_end_time = time.time()
    blink_counter = 0
    
    print("System Started. Entering Calibration...")
    tts.speak("Calibration starting. Please look at the camera and blink naturally.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 1. Processing
        left_ear, right_ear, landmarks = detector.process_frame(frame)
        avg_ear = (left_ear + right_ear) / 2.0
        current_time = time.time()
        
        # Draw Landmarks (Subtle)
        if len(landmarks) > 0:
            for (x, y) in landmarks:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # ---------------------------------------------------------
        # MODE: CALIBRATION
        # ---------------------------------------------------------
        if calibration_active:
            elapsed = current_time - calibration_start_time
            remaining = CALIBRATION_DURATION - elapsed
            
            if remaining > 0:
                calibration_ears.append(avg_ear)
                draw_ui(frame, 'CALIBRATION', {'time_left': remaining}, {})
            else:
                # Calibration Done
                if len(calibration_ears) > 10:
                    # Simple heuristic: 
                    # 5th percentile as "closed eyes" (approx) or min
                    # 95th percentile as "open eyes"
                    # Threshold = Average of those, or slightly lower than "open"
                    
                    cal_array = np.array(calibration_ears)
                    # Filter out zeros (failed detection)
                    cal_array = cal_array[cal_array > 0.0]
                    
                    if len(cal_array) > 0:
                        min_ear = np.min(cal_array) 
                        max_ear = np.max(cal_array)
                        mean_ear = np.mean(cal_array)
                        
                        # A better heuristic for blinks:
                        # Blinks are outliers at the bottom.
                        # We want a threshold that catches them.
                        # Usually threshold ~ 0.2 - 0.25.
                        # Let's set it at (min + mean) / 2? Or (min + max) / 2?
                        # Standard EAR paper suggests ~0.3 for open, ~0.2 or less for closed.
                        # Let's try: 
                        # current_ear_threshold = min_ear + 0.05 # Conservative
                        # OR mean - std_dev?
                        
                        # Let's use a safe fallback if variance is low
                        target_thresh = (min_ear + mean_ear) / 2.0
                        
                        # Safety checks
                        if target_thresh < 0.15: target_thresh = 0.15
                        if target_thresh > 0.35: target_thresh = 0.35
                        
                        current_ear_threshold = target_thresh
                        print(f"Calibration Complete. New Threshold: {current_ear_threshold:.3f}")
                        tts.speak("Calibration complete.")
                    else:
                        print("Calibration failed (no eyes?), using default.")
                
                calibration_active = False
                last_blink_end_time = time.time() # Reset timers

        # ---------------------------------------------------------
        # MODE: ACTIVE
        # ---------------------------------------------------------
        else:
            # Blink Detection
            if avg_ear < current_ear_threshold:
                blink_counter += 1
            else:
                # Eye is open
                if blink_counter >= BLINK_CONSEC_FRAMES:
                    # Blink Logic
                    blink_duration = current_time - blink_start_time
                    
                    signal = "." if blink_duration < DOT_DURATION_THRESHOLD else "-"
                    decoder.add_signal(signal)
                    last_blink_end_time = current_time
                    
                blink_counter = 0
                blinking = False
            
            # Start of blink
            if blink_counter == 1:
                blink_start_time = current_time
                blinking = True
                
            # Pause / Timeout Logic
            if not blinking:
                time_since_last_blink = current_time - last_blink_end_time
                
                if decoder.current_sequence and time_since_last_blink > LETTER_PAUSE_THRESHOLD:
                    decoder.decode_sequence()
                    
                if decoder.current_word and time_since_last_blink > WORD_PAUSE_THRESHOLD:
                    word = decoder.complete_word()
                    if word:
                        print(f"Speaking: {word}")
                        tts.speak(word)
                        
            # UI Updates
            debug_info = {
                'ear': avg_ear,
                'threshold': current_ear_threshold,
                'blinking': blinking
            }
            draw_ui(frame, 'ACTIVE', debug_info, decoder.get_display_text())

        # Display
        cv2.imshow("Blink Morse AI", frame)
        
        # Input Handling
        key = cv2.waitKey(1) & 0xFF
        if key == 27: # Esc
            break
        elif key == ord('r'): # Reset
            decoder.reset()
            calibration_active = True # Allow re-calibration
            calibration_start_time = time.time()
            calibration_ears = []
            print("Resetting...")
        elif key == ord('c'): # Force Calibrate
            calibration_active = True
            calibration_start_time = time.time()
            calibration_ears = []
            
    cap.release()
    cv2.destroyAllWindows()
    tts.stop()

if __name__ == "__main__":
    main()
