# Operation Modes
CALIBRATION = "CALIBRATION"
MODE_SELECTION = "MODE_SELECTION"
PATIENT_MODE = "PATIENT_MODE"
MORSE_MODE = "MORSE_MODE"

# Patient Mode Vocabulary (Short codes)
# Minimized for easy access
PATIENT_VOCAB = {
    ".": "YES",
    "-": "NO",
    "..": "WATER",
    "--": "FOOD",
    ".-": "HELP",
    "-.": "PAIN",
    "...": "BATHROOM",
    "---": "FAMILY"
}

def get_patient_word(sequence):
    """Returns the word corresponding to a sequence, or None."""
    return PATIENT_VOCAB.get(sequence)
