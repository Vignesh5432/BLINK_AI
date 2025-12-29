import cv2
import time
import numpy as np
from config import (
    EAR_THRESHOLD_DEFAULT, BLINK_CONSEC_FRAMES, 
    DOT_DURATION_THRESHOLD, LETTER_PAUSE_THRESHOLD, 
    WORD_PAUSE_THRESHOLD, CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT
)
from blink_detector import BlinkDetector
from morse_logic import MorseDecoder
from tts_engine import TTSEngine
from calibration import Calibrator
from ui_overlay import draw_calibration_ui, draw_mode_selection_ui, draw_active_ui
from modes import PATIENT_MODE, MORSE_MODE, CALIBRATION, MODE_SELECTION

def main():
    # 1. Initialize Components
    detector = BlinkDetector()
    decoder = MorseDecoder()
    tts = TTSEngine()
    calibrator = Calibrator()
    
    # 2. Camera Setup
    # Force High Resolution
    CAM_WIDTH = 1280
    CAM_HEIGHT = 720
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    
    # UI Canvas Constants
    CANVAS_WIDTH = 1920
    CANVAS_HEIGHT = 1080
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # 3. System State
    current_state = CALIBRATION
    calibrator.start()
    
    # Runtime Variables
    current_ear_threshold = EAR_THRESHOLD_DEFAULT
    blink_start_time = 0
    blinking = False
    last_blink_end_time = time.time()
    blink_counter = 0
    
    # Mode-Specific Buffers
    morse_buffer = ""
    
    # Mode Switch Safety
    last_mode_switch_time = 0
    WARMUP_DELAY = 0.5 
    
    # Timing State Tracking
    gap_state = "NONE" # NONE, SYMBOL_GAP, LETTER_GAP, WORD_GAP
    
    tts.speak("Welcome. Starting calibration.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Create dedicated Canvas
        canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)
        
        # Resize frame if needed to fit our slot (optional safety)
        fh, fw, _ = frame.shape
        limit_h = min(fh, CANVAS_HEIGHT)
        limit_w = min(fw, CANVAS_WIDTH)
        canvas[0:limit_h, 0:limit_w] = frame[0:limit_h, 0:limit_w]
            
        # ---------------------------------------------------------
        # COMMON PROCESSING
        # ---------------------------------------------------------
        left_ear, right_ear, landmarks, blink_event = detector.process_frame(frame, current_ear_threshold)
        avg_ear = (left_ear + right_ear) / 2.0
        current_time = time.time()
        
        # Check Warmup Delay
        if current_time - last_mode_switch_time < WARMUP_DELAY:
            blink_event = None # Suppress all input during warmup
        
        # Draw Landmarks (Canvas)
        for (x, y) in landmarks:
             cv2.circle(canvas, (x, y), 1, (0, 255, 0), -1)

        # ---------------------------------------------------------
        # STATE MACHINE
        # ---------------------------------------------------------
        
        if current_state == CALIBRATION:
            calibrator.update(avg_ear)
            draw_calibration_ui(canvas, calibrator)
            
            if not calibrator.is_calibrating:
                current_ear_threshold = calibrator.get_threshold()
                current_state = MODE_SELECTION
                tts.speak("Calibration done. Select mode.")
                
        elif current_state == MODE_SELECTION:
            draw_mode_selection_ui(canvas)
            # Key Handling is below
            
        elif current_state == PATIENT_MODE:
            # ---------------------------
            # STRICT PATIENT MODE TIMING
            # ---------------------------
            # Rule: Accumulate symbols -> Decode ONLY on WORD GAP (2.5s)
            
            if blink_event:
                symbol = "." if blink_event.duration < DOT_DURATION_THRESHOLD else "-"
                decoder.add_signal(symbol) 
                last_blink_end_time = blink_event.end_time
                blinking = False
                
            blinking = detector.is_closed
            
            # Gap Analysis
            time_since_last = current_time - last_blink_end_time
            
            # Identify Gap State
            if time_since_last >= WORD_PAUSE_THRESHOLD:
                # WORD GAP Reached -> Commit Sequence
                if decoder.current_sequence:
                     # For Patient Mode, sequence IS the word identifier
                     word = decoder.decode_sequence()
                     if word:
                         print(f"Patient Command: {word}")
                         tts.speak(word)
                         decoder.complete_word() # Flush buffer
                     else:
                         # Invalid sequence, still flush to reset
                         decoder.reset()
            
            # UI Update
            debug_data = {
                'ear': avg_ear,
                'threshold': current_ear_threshold,
                'blinking': blinking
            }
            draw_active_ui(canvas, current_state, debug_data, decoder.get_display_text())

        elif current_state == MORSE_MODE:
            # ---------------------------
            # STRICT MORSE MODE TIMING
            # ---------------------------
            # Rules:
            # 1. Accumulate symbols in local buffer
            # 2. Local Buffer -> Decoder on LETTER GAP (1.0s)
            # 3. Decoder -> Speak on WORD GAP (2.5s)
            
            if blink_event:
                 symbol = "." if blink_event.duration < DOT_DURATION_THRESHOLD else "-"
                 morse_buffer += symbol
                 last_blink_end_time = blink_event.end_time
                 blinking = False
            
            blinking = detector.is_closed
            
            # Gap Analysis
            gap_duration = current_time - last_blink_end_time
            
            # 1. WORD GAP CHECK (Highest Priority)
            if not blinking and gap_duration >= WORD_PAUSE_THRESHOLD:
                # "Decode any pending symbol buffer"
                if morse_buffer:
                    for s in morse_buffer: 
                        decoder.add_signal(s)
                    decoder.decode_sequence()
                    morse_buffer = ""
                
                # Finalize Word
                if decoder.current_word:
                    word = decoder.complete_word()
                    if word:
                        print(f"Speaking Morse: {word}")
                        tts.speak(word)
                        
            # 2. LETTER GAP CHECK
            elif not blinking and morse_buffer and gap_duration >= LETTER_PAUSE_THRESHOLD:
                # Commit local buffer to decoder
                for s in morse_buffer:
                    decoder.add_signal(s)
                decoder.decode_sequence() # E.g. ".." -> "I"
                morse_buffer = "" # Clear local

            # UI Update
            ui_data = decoder.get_display_text()
            if morse_buffer:
                ui_data['current_signals'] = morse_buffer
            
            debug_data = {
                'ear': avg_ear,
                'threshold': current_ear_threshold,
                'blinking': blinking
            }
            draw_active_ui(canvas, current_state, debug_data, ui_data)

        # ---------------------------------------------------------
        # DISPLAY & INPUT
        # ---------------------------------------------------------
        cv2.imshow("Blink Morse AI", canvas)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27: # ESC
            break
            
        # Global Reset
        if key == ord('c'):
            print("Force Calibration")
            current_state = CALIBRATION
            calibrator.start()
            decoder.reset()
            morse_buffer = ""
            
        # Mode Switching with HARD RESET
        new_mode = None
        if current_state == MODE_SELECTION:
            if key == ord('p'):
                new_mode = PATIENT_MODE
                tts.speak("Patient Mode Active")
            elif key == ord('m'):
                new_mode = MORSE_MODE
                tts.speak("Morse Mode Active")
        
        # While in Active mode, allow switching back to menu
        if key == ord('\t'): 
             current_state = MODE_SELECTION
             tts.speak("Select mode")
             # Reset Everything on exit too
             decoder.reset()
             morse_buffer = ""
             
        if new_mode:
            current_state = new_mode
            decoder.set_mode(new_mode)
            # HARD RESET STATE
            morse_buffer = ""
            decoder.reset()
            last_mode_switch_time = time.time()
            # Also reset blink timers so we don't trigger immediate gaps
            last_blink_end_time = time.time() 

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    tts.stop()

if __name__ == "__main__":
    main()
