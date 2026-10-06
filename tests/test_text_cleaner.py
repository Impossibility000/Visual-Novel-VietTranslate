import time
import unittest
from src.core.text_cleaner import TextCleaner

class TestTextCleaner(unittest.TestCase):
    def test_clean_ruby_tags(self):
        cleaner = TextCleaner()
        
        raw1 = "私[わたし]の名前は太郎[たろう]です。"
        self.assertEqual(cleaner.clean_text(raw1), "私の名前は太郎です。")
        
        raw2 = "彼女{かのじょ}の{瞳|ひとみ}が輝く。"
        self.assertEqual(cleaner.clean_text(raw2), "彼女の瞳が輝く。")
        
        raw3 = "【桜】[r]「おはよう、\\n先輩！」"
        self.assertEqual(cleaner.clean_text(raw3), "【桜】「おはよう、先輩！」")

    def test_clean_control_codes_and_garbage(self):
        cleaner = TextCleaner()
        
        raw = "  \\k[10] Hello  @w @v  World \\c[3]! \r\n\t "
        self.assertEqual(cleaner.clean_text(raw), "Hello World !")

    def test_deduplication(self):
        cleaner = TextCleaner()
        
        text = "こんにちは、世界！"
        self.assertFalse(cleaner.is_duplicate(text, ttl_seconds=1.0))
        self.assertTrue(cleaner.is_duplicate(text, ttl_seconds=1.0))
        self.assertFalse(cleaner.is_duplicate("違うテキスト", ttl_seconds=1.0))

    def test_typewriter_debouncer(self):
        cleaner = TextCleaner()
        
        chunk1 = "こん"
        chunk2 = "こんにち"
        chunk3 = "こんにちは"
        
        self.assertEqual(cleaner.process_typewriter_chunk(chunk1), "こん")
        self.assertEqual(cleaner.process_typewriter_chunk(chunk2), "こんにち")
        self.assertEqual(cleaner.process_typewriter_chunk(chunk3), "こんにちは")

    def test_remove_repeated_phrases(self):
        cleaner = TextCleaner()
        raw = '"Hello world. How are you?" "Hello world. How are you?" "Hello world. How are you?" "I am fine."'
        cleaned = cleaner.clean_text(raw)
        self.assertIn('"Hello world. How are you?"', cleaned)
        self.assertIn('"I am fine."', cleaned)
        self.assertEqual(cleaned.count("Hello world. How are you?"), 1)

    def test_ponscripter_multiline_repetition(self):
        cleaner = TextCleaner()
        raw = (
            "Oh, of course not, my mistake. I see you've changed a lot since we last saw you.\n"
            "Oh, of course not, my mistake. I see you've changed a lot since we last saw you.\n"
            "Oh, of course not, my mistake. I see you've changed a lot since we last saw you.\n"
            "Sheesh, and here you are, old enough to smoke and drink."
        )
        cleaned = cleaner.clean_text(raw)
        self.assertEqual(cleaned.count("Oh, of course not, my mistake"), 1)
        self.assertIn("Sheesh, and here you are", cleaned)

if __name__ == "__main__":
    unittest.main()
