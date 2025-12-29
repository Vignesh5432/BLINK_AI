from config import MORSE_CODE_DICT
from modes import PATIENT_MODE, MORSE_MODE, get_patient_word

class MorseDecoder:
    def __init__(self):
        # Reverse the dictionary for lookup
        self.code_to_char = {v: k for k, v in MORSE_CODE_DICT.items()}
        self.current_sequence = ""
        self.current_word = ""
        self.decoded_sentence = ""
        self.mode = MORSE_MODE # Default

    def set_mode(self, mode):
        self.mode = mode
        self.reset()

    def add_signal(self, signal):
        """Adds a dot (.) or dash (-) to the current sequence."""
        self.current_sequence += signal

    def decode_sequence(self):
        """Decodes the current accumulated sequence into a character or word."""
        if not self.current_sequence:
            return None
        
        result = None
        
        if self.mode == PATIENT_MODE:
            # In Patient Mode, a sequence directly maps to a whole word
            word = get_patient_word(self.current_sequence)
            if word:
                self.current_word = word
                result = word
        else:
            # Morse Mode: Sequence -> Character
            char = self.code_to_char.get(self.current_sequence, "?")
            if char != "?":
                self.current_word += char
                result = char
            
        # Reset sequence after decoding
        completed_sequence = self.current_sequence
        self.current_sequence = ""
        return result

    def complete_word(self):
        """Finalizes the current word and adds it to the sentence."""
        if not self.current_word:
            return None
            
        word = self.current_word
        self.decoded_sentence += " " + word
        self.current_word = ""
        return word

    def get_display_text(self):
        """Returns the current state for UI display."""
        # Clean up double spaces if any
        full_text = self.decoded_sentence.strip()
        current_building_word = self.current_word
        current_signals = self.current_sequence
        
        return {
            "sentence": full_text,
            "current_word": current_building_word,
            "current_signals": current_signals
        }
    
    def reset(self):
        self.current_sequence = ""
        self.current_word = ""
        self.decoded_sentence = ""
