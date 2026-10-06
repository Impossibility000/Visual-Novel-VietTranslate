import unittest
from src.core.local_translator import LocalOfflineTranslator
from src.config.settings import AppSettings
from src.core.translator import AITranslator

class TestLocalTranslator(unittest.TestCase):
    def test_local_translator_singleton(self):
        loc1 = LocalOfflineTranslator.get_instance()
        loc2 = LocalOfflineTranslator.get_instance()
        self.assertIs(loc1, loc2)
        self.assertTrue(loc1.is_available())

    def test_local_offline_translation_en_to_vi(self):
        loc = LocalOfflineTranslator.get_instance()
        result = loc.translate("Hello, world!", "en", "vi")
        self.assertTrue(len(result) > 0)
        self.assertIn("Chào", result)

    def test_local_offline_translation_ja_to_vi(self):
        loc = LocalOfflineTranslator.get_instance()
        result = loc.translate("おはようございます", "ja", "vi")
        self.assertTrue(len(result) > 0)

    def test_translator_with_offline_only_mode(self):
        settings = AppSettings()
        settings.set("offline_only", True)
        translator = AITranslator(settings=settings)
        
        import asyncio
        async def _test():
            res = await translator.translate_full("Hello, friend!", provider="gemini", src_lang="en", tgt_lang="vi")
            return res
        
        res = asyncio.run(_test())
        self.assertTrue(len(res) > 0)
        self.assertNotIn("[Lỗi", res)
