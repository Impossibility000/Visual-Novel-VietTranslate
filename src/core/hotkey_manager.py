import threading
import logging
from typing import Dict, Callable, Optional

logger = logging.getLogger("GlobalHotkeyManager")

class GlobalHotkeyManager:
    """Manages global Windows keyboard shortcuts using pynput."""
    
    def __init__(self):
        self._listener = None
        self._hotkeys_map: Dict[str, Callable[[], None]] = {}
        self._is_active = False

    def register_hotkeys(self, hotkeys_dict: Dict[str, Callable[[], None]]) -> None:
        """Register dictionary mapping '<ctrl>+<f1>' format keys to callbacks."""
        self.stop()
        self._hotkeys_map = dict(hotkeys_dict)
        self.start()

    def start(self) -> None:
        if not self._hotkeys_map or self._is_active:
            return
        
        try:
            from pynput import keyboard
            
            # Format hotkeys for pynput
            formatted = {}
            for key_combo, callback in self._hotkeys_map.items():
                k = key_combo.lower().strip()
                # normalize ctrl+f1 -> <ctrl>+<f1>
                parts = k.split("+")
                normalized_parts = [f"<{p.strip()}>" if not p.strip().startswith("<") else p.strip() for p in parts]
                combo_str = "+".join(normalized_parts)
                formatted[combo_str] = callback

            self._listener = keyboard.GlobalHotKeys(formatted)
            self._listener.start()
            self._is_active = True
            logger.info("Global hotkeys listener started.")
        except Exception as e:
            logger.warning(f"Could not start global hotkeys listener: {e}")

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        self._is_active = False
