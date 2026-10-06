import re
from typing import Dict, Optional

class GlossaryManager:
    """Manages custom terminology, character names, and honorific mapping."""
    
    def __init__(self, initial_rules: Optional[Dict[str, str]] = None):
        self._rules: Dict[str, str] = dict(initial_rules or {})

    def add_rule(self, original: str, translated: str) -> None:
        if original and translated:
            self._rules[original.strip()] = translated.strip()

    def remove_rule(self, original: str) -> None:
        if original in self._rules:
            del self._rules[original]

    def get_rules(self) -> Dict[str, str]:
        return dict(self._rules)

    def set_rules(self, rules: Dict[str, str]) -> None:
        self._rules = dict(rules or {})

    def apply_pre_replace(self, text: str) -> str:
        """Replace exact term matches in source text before feeding to translator if requested."""
        if not text:
            return ""
        result = text
        for orig, target in self._rules.items():
            result = result.replace(orig, target)
        return result

    def format_prompt_instructions(self) -> str:
        """Format glossary rules for injection into LLM system prompt."""
        if not self._rules:
            return ""
        lines = ["[Glossary & Character Name Mapping - Strict Adherence Required]:"]
        for orig, target in self._rules.items():
            lines.append(f"- {orig} -> {target}")
        return "\n".join(lines)
