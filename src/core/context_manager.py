from typing import List, Tuple

class ContextManager:
    """Maintains a rolling ring-buffer of recent conversation turns to provide narrative continuity."""
    
    def __init__(self, max_turns: int = 4):
        self.max_turns = max(1, max_turns)
        self._history: List[Tuple[str, str]] = []

    def add_turn(self, source_text: str, translated_text: str) -> None:
        """Add a newly translated turn (source, translated)."""
        if not source_text or not translated_text:
            return
        
        self._history.append((source_text.strip(), translated_text.strip()))
        if len(self._history) > self.max_turns:
            self._history.pop(0)

    def get_formatted_context(self) -> str:
        """Format the dialogue history for prompt injection."""
        if not self._history:
            return ""
        
        lines = ["[Previous Context / Recent Dialogue History]:"]
        for idx, (src, tgt) in enumerate(self._history, 1):
            lines.append(f"{idx}. {src} -> {tgt}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all stored turns."""
        self._history.clear()

    def get_turns(self) -> List[Tuple[str, str]]:
        return list(self._history)
