import os
import unittest
from src.config.settings import AppSettings
from src.core.text_cleaner import TextCleaner
from src.core.glossary import GlossaryManager
from src.core.context_manager import ContextManager
from src.core.translator import AITranslator

class TestIntegration(unittest.TestCase):
    def test_full_pipeline_flow(self):
        config_file = "tests/temp_integration_settings.json"
        if os.path.exists(config_file):
            os.remove(config_file)
            
        try:
            # 1. Config
            settings = AppSettings(config_path=config_file)
            settings.set_glossary_entry("先輩", "Tiền bối")
            settings.save()
            
            # 2. Cleaner
            cleaner = TextCleaner()
            raw_game_text = "【桜】[r]「おはよう、先輩！\\n今日もいい天気ですね。」"
            cleaned = cleaner.clean_text(raw_game_text)
            self.assertEqual(cleaned, "【桜】「おはよう、先輩！今日もいい天気ですね。」")
            
            # 3. Glossary & Context
            glossary = GlossaryManager(settings.get("glossary", {}))
            context = ContextManager(max_turns=3)
            
            glossary_instr = glossary.format_prompt_instructions()
            self.assertIn("先輩 -> Tiền bối", glossary_instr)
            
            # 4. Translator Prompt
            translator = AITranslator(settings=settings)
            sys_prompt = translator.build_system_prompt(
                src_lang="ja",
                tgt_lang="vi",
                glossary_info=glossary_instr
            )
            full_prompt = translator.build_full_prompt(
                text=cleaned,
                src_lang="ja",
                tgt_lang="vi",
                context=context.get_formatted_context(),
                glossary_info=glossary_instr
            )
            
            self.assertIn("先輩 -> Tiền bối", sys_prompt)
            self.assertIn("おはよう、先輩！", full_prompt)
            
            # 5. Rotate context
            context.add_turn(cleaned, "【Sakura】「Chào buổi sáng, tiền bối! Hôm nay trời đẹp thật nhỉ.」")
            turns = context.get_turns()
            self.assertEqual(len(turns), 1)
            self.assertIn("Chào buổi sáng, tiền bối!", turns[0][1])
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)

if __name__ == "__main__":
    unittest.main()
