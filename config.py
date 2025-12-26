# Morse Code Dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
    ', ': '--..--', '.': '.-.-.-', '?': '..--..', '/': '-..-.', '-': '-....-',
    '(': '-.--.', ')': '-.--.-', ' ': '/'
}

# Blink detection constants
EAR_THRESHOLD_DEFAULT = 0.22  # Eye Aspect Ratio threshold to consider eye closed
BLINK_CONSEC_FRAMES = 2       # Minimum frames to register a blink (filter noise)

# Timing constants (in seconds)
DOT_DURATION_THRESHOLD = 0.4  # Max duration for a DOT
# DASH is whatever is longer than DOT_DURATION_THRESHOLD
LETTER_PAUSE_THRESHOLD = 1.0  # Pause duration to consider end of letter
WORD_PAUSE_THRESHOLD = 2.5    # Pause duration to consider end of word


# Camera settings
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Calibration
CALIBRATION_DURATION = 5.0 # Seconds to calibrate
CALIBRATION_BUFFER_SIZE = 100 # Number of frames to keep for stats
