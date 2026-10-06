import unittest
from unittest.mock import MagicMock
from src.core.tts_player import TTSPlayer

class TestTTSPlayer(unittest.TestCase):
    def test_tts_player_initialization(self):
        player = TTSPlayer()
        self.assertEqual(player.default_voice, "vi-VN-HoaiMyNeural")
        self.assertFalse(player.is_playing())

    def test_tts_voice_mapping(self):
        player = TTSPlayer()
        self.assertIn("ja-JP-NanamiNeural", player.get_available_voices())
        self.assertIn("vi-VN-HoaiMyNeural", player.get_available_voices())

if __name__ == "__main__":
    unittest.main()
