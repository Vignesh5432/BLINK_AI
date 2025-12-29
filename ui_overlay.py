import cv2
import numpy as np
from config import EAR_THRESHOLD_DEFAULT
from modes import PATIENT_VOCAB

# Fonts
FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_GRAY = (200, 200, 200)
COLOR_BG_DARK = (30, 30, 30)

def wrap_text(text, font, font_scale, max_width):
    """Splits text into lines that fit within max_width."""
    if not text:
        return []
    
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        # Test width with new word
        test_line = " ".join(current_line + [word])
        (w, _), _ = cv2.getTextSize(test_line, font, font_scale, 1)
        
        if w > max_width and current_line:
            # Current line is full, push it
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
             current_line.append(word)
             
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_calibration_ui(frame, calibrator):
    h, w, _ = frame.shape
    
    # Check if we are on a large canvas (HD)
    is_hd = w >= 1280
    
    # Top overlay
    cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
    
    cv2.putText(frame, "SYSTEM CALIBRATION", (20, 30), FONT, 0.8, COLOR_YELLOW, 2)
    cv2.putText(frame, "Look at the camera and blink naturally", (20, 60), FONT, 0.6, COLOR_WHITE, 1)
    
    # Progress Bar needs to be centered on the whole screen or video?
    # Let's center on screen for visibility
    bar_width = int(w * 0.6)
    bar_height = 30
    x_start = int((w - bar_width) / 2)
    y_start = h // 2
    
    progress = calibrator.get_progress() / 5.0 # Max 5 seconds
    progress = min(progress, 1.0)
    
    # Background bar
    cv2.rectangle(frame, (x_start, y_start), (x_start + bar_width, y_start + bar_height), (100, 100, 100), -1)
    # Foreground bar
    cv2.rectangle(frame, (x_start, y_start), (x_start + int(bar_width * progress), y_start + bar_height), COLOR_GREEN, -1)
    
    time_left = calibrator.get_remaining_time()
    cv2.putText(frame, f"{time_left:.1f}s", (x_start + bar_width + 10, y_start + 25), FONT, 0.8, COLOR_WHITE, 2)

def draw_mode_selection_ui(frame):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    
    center_x = w // 2 - 100
    
    cv2.putText(frame, "SELECT MODE", (center_x - 50, 200), FONT, 1.5, COLOR_YELLOW, 3)
    cv2.putText(frame, "Press 'P' for PATIENT Mode", (center_x, 300), FONT, 1.0, COLOR_WHITE, 2)
    cv2.putText(frame, "Press 'M' for MORSE Mode", (center_x, 360), FONT, 1.0, COLOR_WHITE, 2)
    cv2.putText(frame, "Press 'C' to Recalibrate", (center_x, 420), FONT, 0.8, COLOR_GRAY, 1)

def draw_active_ui(frame, mode, detector_data, decoder_data):
    h, w, _ = frame.shape
    
    # Assumed Video Layout (Top-Left)
    video_w = 1280
    video_h = 720
    
    # 1. Top Status Bar (Overlay on video for compactness or top of canvas)
    # Let's put it at standard top
    cv2.rectangle(frame, (0, 0), (w, 50), COLOR_BG_DARK, -1)
    
    mode_str = "PATIENT MODE" if mode == "PATIENT_MODE" else "MORSE MODE"
    cv2.putText(frame, mode_str, (20, 35), FONT, 1.0, COLOR_GREEN, 2)
    
    ear = detector_data.get('ear', 0.0)
    thresh = detector_data.get('threshold', 0.0)
    cv2.putText(frame, f"EAR: {ear:.2f} | TH: {thresh:.2f}", (400, 35), FONT, 0.7, COLOR_GRAY, 1)
    
    # Blink Indicator
    is_blinking = detector_data.get('blinking', False)
    color = COLOR_RED if is_blinking else COLOR_GREEN
    # Draw closer to center of status bar or right corner of video
    cv2.circle(frame, (video_w - 50, 25), 15, color, -1)
    
    # 2. Reference Panel (Right Side of Canvas)
    # If we have extra width > 1280, use it
    if w > video_w:
        panel_x = video_w
        cv2.rectangle(frame, (panel_x, 50), (w, h), (20, 20, 20), -1) # Dark Gray Panel
        cv2.putText(frame, "COMMAND LIST", (panel_x + 20, 90), FONT, 1.0, COLOR_YELLOW, 2)
        
        y = 140
        if mode == "PATIENT_MODE":
            for seq, word in PATIENT_VOCAB.items():
                cv2.putText(frame, f"{seq}", (panel_x + 20, y), FONT, 0.8, COLOR_GREEN, 2)
                cv2.putText(frame, f": {word}", (panel_x + 100, y), FONT, 0.8, COLOR_WHITE, 2)
                y += 40
        else:
            common = [('A', '.-'), ('B', '-...'), ('E', '.'), ('T', '-'), ('S', '...'), ('SOS', '...---...')]
            for char, code in common:
                cv2.putText(frame, f"{char} : {code}", (panel_x + 20, y), FONT, 0.8, COLOR_WHITE, 2)
                y += 40
    else:
        # Fallback for small screens (overlay on video right)
        pass 
            
    # 3. Main Decoding Area (Bottom of Canvas)
    # If h > video_h, use it
    start_y = video_h if h > video_h else (h - 150)
    
    cv2.rectangle(frame, (0, start_y), (video_w, h), COLOR_BG_DARK, -1)
    
    # Current Signal
    current_signal = decoder_data.get('current_signals', '')
    cv2.putText(frame, f"Signal: {current_signal}", (20, start_y + 50), FONT, 1.2, COLOR_YELLOW, 2)
    
    # Current Word
    current_word = decoder_data.get('current_word', '')
    cv2.putText(frame, f"Building: {current_word}", (300, start_y + 50), FONT, 1.2, COLOR_GREEN, 2)
    
    # Final Sentence (Wrapped)
    sentence = decoder_data.get('sentence', '')
    
    text_area_width = video_w - 40
    wrapped_lines = wrap_text(sentence, FONT, 1.0, text_area_width)
    
    # Show last 3 lines
    max_lines = 3
    display_lines = wrapped_lines[-max_lines:]
    
    text_y = start_y + 110
    for line in display_lines:
        cv2.putText(frame, line, (20, text_y), FONT, 1.0, COLOR_WHITE, 2)
        text_y += 40

