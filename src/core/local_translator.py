import logging
from typing import Optional, List

logger = logging.getLogger("LocalOfflineTranslator")

class LocalOfflineTranslator:
    """Fast, Zero-Token Offline Translation Engine using Argos Translate."""
    
    _instance = None
    
    def __init__(self):
        self._initialized = False
        self._installed_languages = {}
        self._init_engine()

    @classmethod
    def get_instance(cls) -> 'LocalOfflineTranslator':
        if cls._instance is None:
            cls._instance = LocalOfflineTranslator()
        return cls._instance

    def _init_engine(self) -> None:
        try:
            import argostranslate.translate
            installed = argostranslate.translate.get_installed_languages()
            self._installed_languages = {l.code: l for l in installed}
            self._initialized = True
            logger.info(f"Local Offline Translator initialized with languages: {list(self._installed_languages.keys())}")
        except Exception as e:
            logger.warning(f"Could not initialize local offline translator: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        return self._initialized and len(self._installed_languages) > 0

    def get_installed_language_codes(self) -> List[str]:
        return list(self._installed_languages.keys())

    def translate(self, text: str, src_lang: str = "ja", tgt_lang: str = "vi") -> str:
        """Translate text locally using offline models without internet or API keys."""
        if not text or not text.strip():
            return ""
            
        if not self._initialized:
            self._init_engine()
            if not self._initialized:
                return text

        try:
            import argostranslate.translate
            
            src = self._installed_languages.get(src_lang)
            tgt = self._installed_languages.get(tgt_lang)
            
            if not src or not tgt:
                # Refresh installed list in case newly added
                installed = argostranslate.translate.get_installed_languages()
                self._installed_languages = {l.code: l for l in installed}
                src = self._installed_languages.get(src_lang)
                tgt = self._installed_languages.get(tgt_lang)

            if not src or not tgt:
                logger.warning(f"Language pair {src_lang} -> {tgt_lang} not installed locally.")
                return ""

            translation = src.get_translation(tgt)
            if translation is None:
                logger.warning(f"No direct translation pipeline for {src_lang} -> {tgt_lang}")
                return ""

            result = translation.translate(text)
            return result.strip()
        except Exception as e:
            logger.error(f"Local offline translation error: {e}")
            return ""
