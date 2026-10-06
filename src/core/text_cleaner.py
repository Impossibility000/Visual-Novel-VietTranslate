import re
import time
from difflib import SequenceMatcher
from typing import Optional, Dict, List

class TextCleaner:
    """Pre-processes raw hooked/OCR text, cleans ruby tags/VN codes, strips prompt glyphs, and deduplicates repeated phrases/blocks."""
    
    def __init__(self):
        self._last_text = ""
        self._last_time = 0.0
        self._history_cache: Dict[str, float] = {}
        self._typewriter_buffer = ""
        self._last_typewriter_time = 0.0

    def remove_repeated_phrases(self, text: str) -> str:
        """Collapse repeated multiline blocks or duplicate phrases/sentences (common in PONScripter/VN text hooks)."""
        if not text:
            return ""
        
        # 1. Check lines / paragraphs deduplication
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) > 1:
            # Consecutive identical lines
            deduped_lines: List[str] = []
            for l in lines:
                if not deduped_lines or not self.is_similar(l, deduped_lines[-1], threshold=0.88):
                    deduped_lines.append(l)
            
            # Sub-block repetition: e.g. [A, B, A, B, A, B, C]
            n = len(deduped_lines)
            for k in range(1, max(2, n // 2 + 1)):
                if n >= 2 * k:
                    pattern = deduped_lines[:k]
                    repeat_count = 0
                    idx = 0
                    while idx + k <= n and all(self.is_similar(deduped_lines[idx + j], pattern[j], threshold=0.88) for j in range(k)):
                        repeat_count += 1
                        idx += k
                    if repeat_count > 1:
                        deduped_lines = pattern + deduped_lines[idx:]
                        break
            text = "\n".join(deduped_lines)

        # 2. Check for quoted dialogue blocks: e.g. "..." "..." "..."
        quotes = re.findall(r'("[^"]+"|\'[^\']+\'|【[^】]+】|「[^」]+」)', text)
        if quotes and len(quotes) > 1:
            deduped_quotes: List[str] = []
            for q in quotes:
                clean_q = q.strip()
                if not deduped_quotes or not self.is_similar(clean_q, deduped_quotes[-1], threshold=0.88):
                    deduped_quotes.append(clean_q)
            
            # Sub-block repetition for quotes
            n = len(deduped_quotes)
            for k in range(1, max(2, n // 2 + 1)):
                if n >= 2 * k:
                    pattern = deduped_quotes[:k]
                    repeat_count = 0
                    idx = 0
                    while idx + k <= n and all(self.is_similar(deduped_quotes[idx + j], pattern[j], threshold=0.88) for j in range(k)):
                        repeat_count += 1
                        idx += k
                    if repeat_count > 1:
                        deduped_quotes = pattern + deduped_quotes[idx:]
                        break
            
            if len(deduped_quotes) < len(quotes):
                return "\n".join(deduped_quotes)
                
        return text

    def clean_text(self, raw_text: str) -> str:
        """Strip VN engine tags, ruby annotations, control codes, prompt glyphs, repeated sentences, and normalize whitespace."""
        if not raw_text:
            return ""
        
        text = raw_text
        
        # 1. Remove Ruby syntax:
        # e.g., 私[わたし] -> 私
        text = re.sub(r'([^\s\[\]{}|]+)\[[ぁ-んァ-ン一-龥a-zA-Z0-9]+\]', r'\1', text)
        
        # e.g., 彼女{かのじょ} -> 彼女 (kanji followed by {reading})
        text = re.sub(r'([^\s\[\]{}|]+)\{[ぁ-んァ-ン一-龥a-zA-Z0-9]+\}', r'\1', text)
        
        # e.g., [ruby=reading]kanji[/ruby] or [r]
        text = re.sub(r'\[r(?:uby)?(?:=[^\]]+)?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[/ruby\]', '', text, flags=re.IGNORECASE)
        
        # e.g., {漢字|かんじ} -> 漢字
        text = re.sub(r'\{([^|}]+)(?:\|[^}]+)?\}', r'\1', text)
        
        # 2. Remove VN engine escape codes & control markers
        # e.g., \n, \r, \k[10], \c[3], \v[1], @w, @v, %0, #0
        text = re.sub(r'\\[nr]', ' ', text)
        text = re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?', '', text)
        text = re.sub(r'@[a-zA-Z0-9]+', '', text)
        text = re.sub(r'[%#][0-9]+', '', text)
        
        # 3. Remove trailing VN dialogue prompt glyphs & OCR next-arrow artifacts
        # e.g., "We used to go by boat. ▷", "some text. D", "some text ▼"
        text = re.sub(r'\s+[▷▶▼▽►◄▲■□◆◇●○|_>Ddo]\s*$', '', text)
        text = re.sub(r'[▷▶▼▽►◄▲■□◆◇●○|_>]\s*$', '', text)
        
        # 4. Remove repeated consecutive phrases (PONScripter hook buffer duplication)
        text = self.remove_repeated_phrases(text)
        
        # 5. Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n', text)
        
        # 6. Remove unwanted spaces around Japanese punctuation/brackets
        text = re.sub(r'([【「『])\s+', r'\1', text)
        text = re.sub(r'\s+([】」』、。！？])', r'\1', text)
        text = re.sub(r'([、。！？])\s+([ぁ-んァ-ン一-龥])', r'\1\2', text)
        
        return text.strip()

    def is_similar(self, s1: str, s2: str, threshold: float = 0.88) -> bool:
        """Check if two strings are substantially identical (fuzzy match for OCR noise & typing)."""
        if not s1 or not s2:
            return s1 == s2
        if s1 == s2:
            return True
        # If one is a prefix/suffix of the other with minor tail difference (prompt cursor)
        if (s1.startswith(s2) or s2.startswith(s1)) and abs(len(s1) - len(s2)) <= 4:
            return True
        ratio = SequenceMatcher(None, s1, s2).ratio()
        return ratio >= threshold

    def is_duplicate(self, text: str, ttl_seconds: float = 4.0) -> bool:
        """Check if this text is identical or fuzzy-identical to the current active line or recent history."""
        if not text:
            return True
        
        # Direct check with last processed text
        if self.is_similar(text, self._last_text, threshold=0.88):
            return True
        
        now = time.time()
        # Clean up stale cache
        self._history_cache = {k: v for k, v in self._history_cache.items() if now - v < ttl_seconds * 3}
        
        # Check against recent cached texts
        for cached_text, timestamp in self._history_cache.items():
            if now - timestamp < ttl_seconds and self.is_similar(text, cached_text, threshold=0.88):
                return True
        
        self._history_cache[text] = now
        self._last_text = text
        return False

    def process_typewriter_chunk(self, new_text: str, timeout_ms: float = 400.0) -> Optional[str]:
        """Track progressive typing. Returns the latest cleaned text."""
        cleaned = self.clean_text(new_text)
        if not cleaned:
            return None
        
        now = time.time()
        # If it's an extension of the current buffer within timeout, update buffer
        if self._typewriter_buffer and cleaned.startswith(self._typewriter_buffer) and (now - self._last_typewriter_time) < (timeout_ms / 1000.0):
            self._typewriter_buffer = cleaned
            self._last_typewriter_time = now
            return cleaned
        
        self._typewriter_buffer = cleaned
        self._last_typewriter_time = now
        return cleaned
