import os
import json
import unittest
from src.config.settings import AppSettings

class TestSettings(unittest.TestCase):
    def test_default_settings_initialization(self):
        config_file = "tests/temp_test_settings.json"
        if os.path.exists(config_file):
            os.remove(config_file)
        try:
            settings = AppSettings(config_path=config_file)
            self.assertEqual(settings.get("selected_provider"), "gemini")
            self.assertEqual(settings.get("source_language"), "ja")
            self.assertEqual(settings.get("target_language"), "vi")
            self.assertEqual(settings.get("overlay")["font_size"], 18)
            self.assertTrue(os.path.exists(config_file))
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)

    def test_save_and_reload_settings(self):
        config_file = "tests/temp_test_settings2.json"
        if os.path.exists(config_file):
            os.remove(config_file)
        try:
            settings = AppSettings(config_path=config_file)
            settings.set("selected_provider", "deepseek")
            settings.set_provider_key("deepseek", "sk-test-key-123")
            settings.save()
            
            # Reload from disk
            new_settings = AppSettings(config_path=config_file)
            self.assertEqual(new_settings.get("selected_provider"), "deepseek")
            self.assertEqual(new_settings.get_provider_key("deepseek"), "sk-test-key-123")
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)

    def test_glossary_management(self):
        config_file = "tests/temp_test_settings3.json"
        if os.path.exists(config_file):
            os.remove(config_file)
        try:
            settings = AppSettings(config_path=config_file)
            settings.set_glossary_entry("先輩", "Tiền bối")
            settings.set_glossary_entry("俺", "Tôi")
            settings.save()
            
            self.assertEqual(settings.get("glossary")["先輩"], "Tiền bối")
            settings.remove_glossary_entry("俺")
            self.assertNotIn("俺", settings.get("glossary"))
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)

if __name__ == "__main__":
    unittest.main()
