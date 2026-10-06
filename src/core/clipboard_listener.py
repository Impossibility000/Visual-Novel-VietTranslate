import sys
import ctypes
import logging
from typing import Callable, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QClipboard

logger = logging.getLogger("ClipboardListener")

# Setup 64-bit safe Win32 API signatures for fallback
if sys.platform == "win32":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = ctypes.c_bool
    
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool

class ClipboardListener:
    """Robust Clipboard Monitor using Qt event-driven dataChanged with 64-bit Win32 safety."""
    
    def __init__(self, poll_interval: float = 0.1):
        self.poll_interval = poll_interval
        self._callback: Optional[Callable[[str], None]] = None
        self._running = False
        self._paused = False
        self._last_clipboard_text = ""
        self._qt_connected = False

    def set_callback(self, callback: Callable[[str], None]) -> None:
        self._callback = callback

    def is_running(self) -> bool:
        return self._running

    def is_paused(self) -> bool:
        return self._paused

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._paused = False
        
        # Connect to Qt's event-driven clipboard signal if QApplication exists
        app = QApplication.instance()
        if app is not None:
            clipboard = QApplication.clipboard()
            if not self._qt_connected:
                clipboard.dataChanged.connect(self._on_qt_clipboard_changed)
                self._qt_connected = True
            self._last_clipboard_text = clipboard.text()
        else:
            self._last_clipboard_text = self._get_win32_clipboard_text()

    def stop(self) -> None:
        self._running = False
        if self._qt_connected:
            app = QApplication.instance()
            if app is not None:
                try:
                    QApplication.clipboard().dataChanged.disconnect(self._on_qt_clipboard_changed)
                except Exception:
                    pass
            self._qt_connected = False

    def _on_qt_clipboard_changed(self) -> None:
        if not self._running or self._paused:
            return
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text and text != self._last_clipboard_text:
                self._last_clipboard_text = text
                self._process_new_text(text)
        except Exception as e:
            logger.error(f"Error reading Qt clipboard: {e}")

    def _process_new_text(self, text: str) -> None:
        if self._paused or not text or not text.strip():
            return
        if self._callback:
            try:
                self._callback(text.strip())
            except Exception as e:
                logger.error(f"[ClipboardListener] Callback error: {e}")

    def _get_win32_clipboard_text(self) -> str:
        """64-bit safe Win32 clipboard text reading."""
        if sys.platform != "win32":
            return ""
        
        CF_UNICODETEXT = 13
        
        if not user32.OpenClipboard(None):
            return ""
        
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            
            p_data = kernel32.GlobalLock(handle)
            if not p_data:
                return ""
            
            try:
                text = ctypes.c_wchar_p(p_data).value or ""
                return text
            finally:
                kernel32.GlobalUnlock(handle)
        except Exception:
            return ""
        finally:
            user32.CloseClipboard()
