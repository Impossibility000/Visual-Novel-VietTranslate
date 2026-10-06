import unittest
from src.core.glossary import GlossaryManager

class TestGlossary(unittest.TestCase):
    def test_glossary_add_remove(self):
        glossary = GlossaryManager()
        glossary.add_rule("先輩", "Tiền bối")
        glossary.add_rule("桜", "Sakura")
        
        self.assertEqual(glossary.get_rules(), {"先輩": "Tiền bối", "桜": "Sakura"})
        glossary.remove_rule("桜")
        self.assertNotIn("桜", glossary.get_rules())

    def test_glossary_prompt_formatting(self):
        glossary = GlossaryManager()
        glossary.add_rule("俺", "Tôi")
        glossary.add_rule("美雪", "Miyuki")
        
        formatted = glossary.format_prompt_instructions()
        self.assertIn("俺 -> Tôi", formatted)
        self.assertIn("美雪 -> Miyuki", formatted)

    def test_glossary_apply_pre_replace(self):
        glossary = GlossaryManager()
        glossary.add_rule("【桜】", "【Sakura】")
        
        text = "【桜】「こんにちは！」"
        replaced = glossary.apply_pre_replace(text)
        self.assertEqual(replaced, "【Sakura】「こんにちは！」")

if __name__ == "__main__":
    unittest.main()
