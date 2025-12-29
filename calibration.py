import time
import numpy as np
from config import CALIBRATION_DURATION, EAR_THRESHOLD_DEFAULT

class Calibrator:
    def __init__(self):
        self.start_time = None
        self.ears = []
        self.is_calibrating = False
        self.calculated_threshold = EAR_THRESHOLD_DEFAULT

    def start(self):
        self.start_time = time.time()
        self.ears = []
        self.is_calibrating = True
        print("Calibration started.")

    def update(self, ear):
        if not self.is_calibrating:
            return

        self.ears.append(ear)
        
        elapsed = time.time() - self.start_time
        if elapsed >= CALIBRATION_DURATION:
            self.complete_calibration()

    def get_progress(self):
        if not self.is_calibrating or self.start_time is None:
            return 0.0
        elapsed = time.time() - self.start_time
        return min(elapsed, CALIBRATION_DURATION)

    def get_remaining_time(self):
        if not self.is_calibrating or self.start_time is None:
            return 0.0
        elapsed = time.time() - self.start_time
        return max(0.0, CALIBRATION_DURATION - elapsed)

    def complete_calibration(self):
        self.is_calibrating = False
        
        if not self.ears:
            print("Calibration failed: No data collected.")
            return

        ear_array = np.array(self.ears)
        # Remove zeros
        ear_array = ear_array[ear_array > 0.0]

        if len(ear_array) == 0:
             print("Calibration failed: All EARs were zero.")
             return

        # Simple robust statistics
        # We assume the user spent most of the time with eyes open
        # But also blinked naturally.
        
        # 1. Estimate Open Eye EAR (Median is robust against blinks)
        median_ear = np.median(ear_array)
        
        # 2. Check for blinks (lower values)
        # We want a threshold that separates the blinks from the open state.
        # A simple adaptive approach: 70% of the median? 
        # Or (Min + Median) / 2?
        
        min_ear = np.min(ear_array)
        
        # Heuristic: Threshold is halfway between the minimum seen (blink) and the median (open)
        # But safeguards to prevent crazy values.
        
        calculated = (min_ear + median_ear) / 2.0
        
        # Clamp to reasonable bounds
        if calculated < 0.15: calculated = 0.15
        if calculated > 0.35: calculated = 0.35
        
        self.calculated_threshold = calculated
        print(f"Calibration Complete. Median: {median_ear:.3f}, Min: {min_ear:.3f}, Thresh: {self.calculated_threshold:.3f}")

    def get_threshold(self):
        return self.calculated_threshold
