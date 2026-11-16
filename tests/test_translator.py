import unittest
from src.core.translator import AITranslator
from src.config.settings import AppSettings

class TestTranslator(unittest.TestCase):
    def test_translator_system_prompt_builder(self):
        settings = AppSettings()
        translator = AITranslator(settings=settings)
        
        sys_prompt = translator.build_system_prompt(
            src_lang="ja",
            tgt_lang="vi",
            glossary_info="- 先輩 -> Tiền bối"
        )
        user_prompt = translator.build_full_prompt(
            text="おはよう、先輩！",
            src_lang="ja",
            tgt_lang="vi",
            context="1. こんにちは -> Xin chào",
            glossary_info="- 先輩 -> Tiền bối"
        )
        
        self.assertIn("Tiền bối", sys_prompt)
        self.assertIn("おはよう、先輩！", user_prompt)
        self.assertIn("Xin chào", user_prompt)

    def test_gemini_streaming_parser(self):
        settings = AppSettings()
        translator = AITranslator(settings=settings)
        
        mock_sse_lines = [
            'data: {"candidates": [{"content": {"parts": [{"text": "Chào "}]}}]}\n\n',
            'data: {"candidates": [{"content": {"parts": [{"text": "buổi sáng, "}]}}]}\n\n',
            'data: {"candidates": [{"content": {"parts": [{"text": "tiền bối!"}]}}]}\n\n'
        ]
        
        parsed = []
        for line in mock_sse_lines:
            chunk = translator.parse_gemini_sse_line(line)
            if chunk:
                parsed.append(chunk)
                
        self.assertEqual("".join(parsed), "Chào buổi sáng, tiền bối!")

    def test_openai_streaming_parser(self):
        settings = AppSettings()
        translator = AITranslator(settings=settings)
        
        mock_sse_lines = [
            'data: {"choices": [{"delta": {"content": "Em "}}]}',
            'data: {"choices": [{"delta": {"content": "yêu "}}]}',
            'data: {"choices": [{"delta": {"content": "anh!"}}]}',
            'data: [DONE]'
        ]
        
        parsed = []
        for line in mock_sse_lines:
            chunk = translator.parse_openai_sse_line(line)
            if chunk:
                parsed.append(chunk)
                
        self.assertEqual("".join(parsed), "Em yêu anh!")

    def test_sanitize_translation_output(self):
        # Test markdown stripping
        res1 = AITranslator.sanitize_translation_output("```markdown\nChào bạn!\n```")
        self.assertEqual(res1, "Chào bạn!")
        
        # Test prefix stripping
        res2 = AITranslator.sanitize_translation_output("Bản dịch tiếng Việt: Em chào anh!")
        self.assertEqual(res2, "Em chào anh!")
        
        # Test outer quotes stripping
        res3 = AITranslator.sanitize_translation_output('"Đây là câu thoại."')
        self.assertEqual(res3, "Đây là câu thoại.")

    def test_hybrid_token_optimization(self):
        settings = AppSettings()
        translator = AITranslator(settings=settings)
        
        std_sys = translator.build_system_prompt(src_lang="ja", tgt_lang="vi")
        hybrid_sys = translator.build_system_prompt(src_lang="ja", tgt_lang="vi", local_draft="Xin chào")
        
        # Hybrid prompt should be significantly more compact than standard prompt
        self.assertLess(len(hybrid_sys), len(std_sys))
        self.assertIn("Local Draft", hybrid_sys)

    def test_cache_and_bypass_fallback(self):
        import asyncio
        settings = AppSettings()
        settings.set_provider_key("gemini", "")
        translator = AITranslator(settings=settings)
        
        async def _run():
            # 1. With bypass_fallback=True, missing key must return error
            err_res = await translator.translate_full("こんにちは", provider="gemini", bypass_fallback=True)
            self.assertIn("[Lỗi", err_res)
            
            # 2. Add to cache
            translator._cache[("こんにちは", "ja", "vi")] = "Xin chào (cached)"
            
            # 3. Subsequent translation hits cache directly (0 token)
            cached_res = await translator.translate_full("こんにちは", provider="gemini", bypass_fallback=False)
            self.assertEqual(cached_res, "Xin chào (cached)")

        asyncio.run(_run())

if __name__ == "__main__":
    unittest.main()
