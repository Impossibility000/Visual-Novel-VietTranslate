import unittest
from unittest.mock import MagicMock
from src.core.clipboard_listener import ClipboardListener

class TestClipboardListener(unittest.TestCase):
    def test_clipboard_listener_state(self):
        listener = ClipboardListener(poll_interval=0.05)
        self.assertFalse(listener.is_running())
        
        mock_callback = MagicMock()
        listener.set_callback(mock_callback)
        
        # Test text dispatching
        listener._process_new_text("テストメッセージ")
        mock_callback.assert_called_once_with("テストメッセージ")

    def test_clipboard_listener_pause(self):
        listener = ClipboardListener(poll_interval=0.05)
        mock_callback = MagicMock()
        listener.set_callback(mock_callback)
        
        listener.pause()
        self.assertTrue(listener.is_paused())
        
        listener._process_new_text("Ignored because paused")
        mock_callback.assert_not_called()
        
        listener.resume()
        self.assertFalse(listener.is_paused())
        listener._process_new_text("Received now")
        mock_callback.assert_called_once_with("Received now")

if __name__ == "__main__":
    unittest.main()
