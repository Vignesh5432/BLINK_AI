import unittest
from morse_logic import MorseDecoder

class TestMorseDecoder(unittest.TestCase):
    def setUp(self):
        self.decoder = MorseDecoder()

    def test_basic_decode(self):
        # Test 'A' (.-)
        self.decoder.add_signal('.')
        self.decoder.add_signal('-')
        self.assertEqual(self.decoder.decode_sequence(), 'A')

    def test_word_building(self):
        # Test "HI"
        # H (....)
        for _ in range(4):
            self.decoder.add_signal('.')
        self.decoder.decode_sequence()
        
        # I (..)
        for _ in range(2):
            self.decoder.add_signal('.')
        self.decoder.decode_sequence()
        
        self.assertEqual(self.decoder.current_word, "HI")
        
        # Complete word
        final_word = self.decoder.complete_word()
        self.assertEqual(final_word, "HI")
        self.assertEqual(self.decoder.decoded_sentence.strip(), "HI")

    def test_reset(self):
        self.decoder.add_signal('.')
        self.decoder.reset()
        self.assertEqual(self.decoder.current_sequence, "")
        self.assertEqual(self.decoder.current_word, "")

if __name__ == '__main__':
    unittest.main()
