import unittest
from src.core.context_manager import ContextManager

class TestContextManager(unittest.TestCase):
    def test_context_buffer_add_and_format(self):
        ctx = ContextManager(max_turns=3)
        
        ctx.add_turn("おはようございます。", "Chào buổi sáng.")
        ctx.add_turn("今日もいい天気ですね。", "Hôm nay trời đẹp thật nhỉ.")
        
        formatted = ctx.get_formatted_context()
        self.assertIn("おはようございます。 -> Chào buổi sáng.", formatted)
        self.assertIn("今日もいい天気ですね。 -> Hôm nay trời đẹp thật nhỉ.", formatted)

    def test_context_buffer_max_capacity(self):
        ctx = ContextManager(max_turns=2)
        
        ctx.add_turn("Line 1", "Dòng 1")
        ctx.add_turn("Line 2", "Dòng 2")
        ctx.add_turn("Line 3", "Dòng 3")
        
        formatted = ctx.get_formatted_context()
        # Line 1 should have rotated out
        self.assertNotIn("Line 1", formatted)
        self.assertIn("Line 2", formatted)
        self.assertIn("Line 3", formatted)

    def test_context_clear(self):
        ctx = ContextManager()
        ctx.add_turn("Text", "Dịch")
        ctx.clear()
        self.assertEqual(ctx.get_formatted_context(), "")

if __name__ == "__main__":
    unittest.main()
