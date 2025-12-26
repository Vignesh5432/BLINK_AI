# Blink Morse AI

A real-time, local AI system that converts eye blinks into Morse code, text, and speech. 
Designed for assistive communication and silent messaging.

## Features
- **Real-time Blink Detection**: Uses MediaPipe Face Mesh to detect blinks via webcam.
- **Morse Decoding**: Converts short blinks (.) and long blinks (-) into text.
- **Text-to-Speech**: Speaks the decoded words offline using `pyttsx3`.
- **Privacy First**: All processing is local. No cloud, no internet required.

## Requirements
- Python 3.x
- Webcam

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```bash
   python app.py
   ```
2. **Calibration**:
   - Ensure your face is well-lit and the camera is stable.
   - Look at the camera. Green dots should appear on your eyes.
   - The EAR (Eye Aspect Ratio) value is displayed.

3. **Communication**:
   - **Dot (.)**: Blink quickly (< 0.4s).
   - **Dash (-)**: Close eyes for a bit longer (> 0.4s).
   - **Letter Space**: Wait ~1 second after a sequence to finalize the letter.
   - **Word Space**: Wait ~2.5 seconds to finalize the word and hear it spoken.

4. **Controls**:
   - `ESC`: Exit the application.
   - `r`: Reset the current text buffers.

## Configuration
You can adjust timing thresholds in `config.py` if the detection is too fast or too slow for your preference.
