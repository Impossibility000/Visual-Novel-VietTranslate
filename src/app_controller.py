import os
import sys
import asyncio
import threading
import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from src.config.settings import AppSettings
from src.core.text_cleaner import TextCleaner
from src.core.glossary import GlossaryManager
from src.core.context_manager import ContextManager
from src.core.translator import AITranslator
from src.core.clipboard_listener import ClipboardListener
from src.core.ocr_engine import OCREngine
from src.core.tts_player import TTSPlayer
from src.core.hotkey_manager import GlobalHotkeyManager

from src.ui.main_window import MainWindow
from src.ui.overlay_window import OverlayWindow
from src.ui.backlog_window import BacklogWindow
from src.ui.region_selector import RegionSelectorDialog

logger = logging.getLogger("AppController")

class AppController(QObject):
    """Central Controller and Event Hub for the AetherVN Application."""
    
    # Internal Qt signals for cross-thread communication
    sig_raw_text_received = Signal(str)
    sig_translation_chunk = Signal(str)
    sig_translation_complete = Signal(str, str)  # (source, translated)
    sig_error = Signal(str)

    def __init__(self, settings_path: str = "config/settings.json"):
        super().__init__()
        self.settings = AppSettings(config_path=settings_path)
        
        # Core Engines
        self.cleaner = TextCleaner()
        self.glossary = GlossaryManager(self.settings.get("glossary", {}))
        self.context = ContextManager(max_turns=4)
        self.translator = AITranslator(settings=self.settings)
        self.clipboard_listener = ClipboardListener(poll_interval=0.1)
        self.ocr_engine = OCREngine()
        self.tts_player = TTSPlayer(self.settings.get("tts", {}).get("voice", "vi-VN-HoaiMyNeural"))
        self.hotkey_manager = GlobalHotkeyManager()
        
        # State
        self.is_active = False
        self._current_source_text = ""
        self._current_translated_text = ""
        
        # UI Windows
        self.main_window = MainWindow(settings=self.settings)
        self.overlay_window = OverlayWindow(settings_dict=self.settings.get("overlay", {}))
        self.backlog_window = BacklogWindow()
        self.region_dialog = RegionSelectorDialog()
        
        # OCR Timer
        self.ocr_timer = QTimer(self)
        self.ocr_timer.setInterval(self.settings.get("ocr", {}).get("scan_interval_ms", 350))
        self.ocr_timer.timeout.connect(self._on_ocr_timer_tick)
        
        # Dedicated Async Worker Thread with Persistent Event Loop (enables HTTP Keep-Alive connection pooling)
        self._async_loop = asyncio.new_event_loop()
        self._async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._async_thread.start()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup)

        self._wire_signals()
        self._setup_hotkeys()

    def _run_async_loop(self):
        asyncio.set_event_loop(self._async_loop)
        self._async_loop.run_forever()

    def cleanup(self):
        """Clean shutdown of background services and HTTP connection pools."""
        self.is_active = False
        if hasattr(self, "ocr_timer") and self.ocr_timer.isActive():
            self.ocr_timer.stop()
        if hasattr(self, "clipboard_listener"):
            self.clipboard_listener.stop()
        if hasattr(self, "hotkey_manager"):
            self.hotkey_manager.stop()
        if hasattr(self, "overlay_window"):
            self.overlay_window.close()
        if hasattr(self, "backlog_window"):
            self.backlog_window.close()
        if hasattr(self, "_async_loop") and self._async_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self.translator.close(), self._async_loop)
                future.result(timeout=1.5)
            except Exception:
                pass
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)

    def _wire_signals(self):
        # Cross-thread signals
        self.sig_raw_text_received.connect(self._handle_raw_text)
        self.sig_translation_chunk.connect(self.overlay_window.append_chunk)
        self.sig_translation_complete.connect(self._handle_translation_complete)
        self.sig_error.connect(self._handle_error)

        # MainWindow signals
        self.main_window.start_requested.connect(self.start_translation)
        self.main_window.pause_requested.connect(self.pause_translation)
        self.main_window.test_api_requested.connect(self._test_api_connection)
        self.main_window.select_ocr_region_requested.connect(self.prompt_select_ocr_region)
        self.main_window.toggle_overlay_requested.connect(self.toggle_overlay_visibility)
        self.main_window.toggle_backlog_requested.connect(self.toggle_backlog_visibility)

        # OverlayWindow signals
        self.overlay_window.geometry_changed.connect(self._on_overlay_geometry_changed)
        self.overlay_window.replay_tts_requested.connect(self._play_tts_voice)
        self.overlay_window.toggle_backlog_requested.connect(self.toggle_backlog_visibility)
        self.overlay_window.font_size_changed.connect(self._on_overlay_font_size_changed)

        # BacklogWindow signals
        self.backlog_window.tts_requested.connect(self._play_tts_voice)

        # Mechanism toggles
        self.main_window.chk_ocr.stateChanged.connect(self._on_ocr_checkbox_changed)
        self.main_window.chk_clipboard.stateChanged.connect(self._on_clipboard_checkbox_changed)
        self.main_window.appearance_changed.connect(self._on_appearance_changed)

        # RegionSelector signals
        self.region_dialog.region_selected.connect(self._on_ocr_region_selected)

        # Clipboard callback
        self.clipboard_listener.set_callback(lambda text: self.sig_raw_text_received.emit(text))

    def _setup_hotkeys(self):
        hotkeys_map = {
            "<ctrl>+<f1>": lambda: QTimer.singleShot(0, self.toggle_click_through),
            "<ctrl>+<f2>": lambda: QTimer.singleShot(0, self.toggle_pause_resume),
            "<ctrl>+<f3>": lambda: QTimer.singleShot(0, self.prompt_select_ocr_region),
            "<ctrl>+<f4>": lambda: QTimer.singleShot(0, self.toggle_overlay_visibility),
            "<ctrl>+<f5>": lambda: QTimer.singleShot(0, self.replay_latest_tts)
        }
        self.hotkey_manager.register_hotkeys(hotkeys_map)

    def start(self):
        """Show main window and start background services."""
        self.main_window.show()
        self.overlay_window.show()
        self.start_translation()

    def start_translation(self):
        self.is_active = True
        self.clipboard_listener.start()
        self.clipboard_listener.resume()
        
        # Start OCR timer if enabled
        if self.settings.get("ocr", {}).get("enabled", False):
            self.ocr_timer.start()

    def pause_translation(self):
        self.is_active = False
        self.clipboard_listener.pause()
        self.ocr_timer.stop()

    def toggle_pause_resume(self):
        if self.is_active:
            self.pause_translation()
            self.main_window._toggle_running()
        else:
            self.start_translation()
            self.main_window._toggle_running()

    def toggle_click_through(self):
        current = self.overlay_window.click_through
        self.overlay_window.set_click_through(not current)

    def toggle_overlay_visibility(self):
        if self.overlay_window.isVisible():
            self.overlay_window.hide()
        else:
            self.overlay_window.show()
            self.overlay_window.raise_()

    def toggle_backlog_visibility(self):
        if self.backlog_window.isVisible():
            self.backlog_window.hide()
        else:
            self.backlog_window.show()
            self.backlog_window.raise_()

    def prompt_select_ocr_region(self):
        self.region_dialog.show()
        self.region_dialog.raise_()

    def _on_ocr_region_selected(self, x: int, y: int, w: int, h: int):
        self.ocr_engine.set_region(x, y, w, h)
        ocr_cfg = self.settings.get("ocr", {})
        ocr_cfg["region"] = [x, y, w, h]
        ocr_cfg["enabled"] = True
        self.settings.set("ocr", ocr_cfg)
        self.settings.save()
        self.main_window.chk_ocr.setChecked(True)
        if self.is_active:
            self.ocr_timer.start()

    def _on_ocr_checkbox_changed(self, state: int):
        is_checked = (state == 2 or state == Qt.CheckState.Checked.value if hasattr(Qt.CheckState, 'Checked') else bool(state))
        if self.is_active:
            if is_checked:
                self.ocr_timer.start()
            else:
                self.ocr_timer.stop()

    def _on_clipboard_checkbox_changed(self, state: int):
        is_checked = (state == 2 or state == Qt.CheckState.Checked.value if hasattr(Qt.CheckState, 'Checked') else bool(state))
        if is_checked and self.is_active:
            self.clipboard_listener.resume()
        else:
            self.clipboard_listener.pause()

    def _on_ocr_timer_tick(self):
        if not self.is_active or not self.settings.get("ocr", {}).get("enabled", False):
            return
        
        if getattr(self, "_ocr_busy", False):
            return
        
        self._ocr_busy = True
        
        # Run OCR in thread to avoid UI stutter
        def _scan():
            try:
                text = self.ocr_engine.scan_once()
                if text:
                    self.sig_raw_text_received.emit(text)
            except Exception as e:
                logger.error(f"OCR scan tick error: {e}")
            finally:
                self._ocr_busy = False

        threading.Thread(target=_scan, daemon=True).start()

    @Slot(str)
    def _handle_raw_text(self, raw_text: str):
        if not self.is_active or not raw_text:
            return
        
        # 1. Clean VN tags, ruby, prompt glyphs
        cleaned = self.cleaner.clean_text(raw_text)
        if not cleaned or len(cleaned) < 2:
            return
        
        # 2. If already translating or displaying this text (or fuzzy match), ignore
        curr = getattr(self, "_current_source_text", "")
        if curr and self.cleaner.is_similar(cleaned, curr, threshold=0.88):
            return
        
        # 3. Check typewriter & fuzzy deduplication
        if self.cleaner.is_duplicate(cleaned, ttl_seconds=4.0):
            return
        
        # 4. Refresh glossary from settings
        self.glossary.set_rules(self.settings.get("glossary", {}))
        
        self._current_source_text = cleaned
        self._is_translating = True
        self.overlay_window.update_text(source=cleaned, translated="", is_streaming=True)
        
        # 5. Dispatch Async Translation via persistent Event Loop
        src_lang = self.settings.get("source_language", "ja")
        tgt_lang = self.settings.get("target_language", "vi")
        context_str = self.context.get_formatted_context()
        glossary_str = self.glossary.format_prompt_instructions()
        provider = self.settings.get("selected_provider", "gemini")

        self._dispatch_translation(cleaned, provider, src_lang, tgt_lang, context_str, glossary_str)

    def _dispatch_translation(self, text: str, provider: str, src_lang: str, tgt_lang: str, context: str, glossary: str):
        async def _do_stream():
            try:
                accumulated = []
                async for chunk in self.translator.translate_stream(text, provider, src_lang, tgt_lang, context, glossary):
                    accumulated.append(chunk)
                    self.sig_translation_chunk.emit(chunk)
                
                raw_translated = "".join(accumulated).strip()
                full_translated = self.translator.sanitize_translation_output(raw_translated)
                if full_translated and not full_translated.startswith("[Lỗi") and "Error" not in full_translated:
                    cache_key = (text.strip(), src_lang, tgt_lang)
                    if len(self.translator._cache) >= self.translator._max_cache_size:
                        self.translator._cache.pop(next(iter(self.translator._cache)))
                    self.translator._cache[cache_key] = full_translated
                self.sig_translation_complete.emit(text, full_translated)
            except Exception as e:
                logger.error(f"Stream translation error: {e}")
                self.sig_error.emit(str(e))

        if hasattr(self, "_async_loop") and self._async_loop.is_running():
            asyncio.run_coroutine_threadsafe(_do_stream(), self._async_loop)
        else:
            threading.Thread(target=lambda: asyncio.run(_do_stream()), daemon=True).start()

    def _run_async_translation(self, text: str, provider: str, src_lang: str, tgt_lang: str, context: str, glossary: str):
        """Backwards compatibility helper."""
        self._dispatch_translation(text, provider, src_lang, tgt_lang, context, glossary)

    @Slot(str, str)
    def _handle_translation_complete(self, source: str, translated: str):
        self._is_translating = False
        self.overlay_window.set_streaming_done()
        self.overlay_window.update_text(source=source, translated=translated, is_streaming=False)
        self._current_translated_text = translated
        
        # Add to context memory
        self.context.add_turn(source, translated)
        
        # Add to dialogue history backlog
        self.backlog_window.add_entry(source, translated)
        
        # Update main window latest line preview
        self.main_window.update_latest_dialogue(source, translated)
        
        # Trigger TTS if auto-read is enabled
        if self.settings.get("tts", {}).get("enabled", False):
            self._play_tts_voice(translated)

    def _play_tts_voice(self, text: str):
        tts_cfg = self.settings.get("tts", {})
        voice = tts_cfg.get("voice", "vi-VN-HoaiMyNeural")
        rate = tts_cfg.get("rate", "+0%")
        self.tts_player.play_async(text, voice=voice, rate=rate)

    def replay_latest_tts(self):
        if self._current_translated_text:
            self._play_tts_voice(self._current_translated_text)

    def _on_overlay_geometry_changed(self, x: int, y: int, w: int, h: int):
        ov = self.settings.get("overlay", {})
        ov["geometry"] = [x, y, w, h]
        self.settings.set("overlay", ov)
        self.settings.save()
        if hasattr(self.main_window, 'sp_overlay_width') and hasattr(self.main_window, 'sp_overlay_height'):
            self.main_window.sp_overlay_width.blockSignals(True)
            self.main_window.sp_overlay_height.blockSignals(True)
            self.main_window.sp_overlay_width.setValue(w)
            self.main_window.sp_overlay_height.setValue(h)
            self.main_window.sp_overlay_width.blockSignals(False)
            self.main_window.sp_overlay_height.blockSignals(False)

    def _on_overlay_font_size_changed(self, new_size: int):
        ov = self.settings.get("overlay", {})
        ov["font_size"] = new_size
        self.settings.set("overlay", ov)
        self.settings.save()
        if hasattr(self.main_window, 'sp_font_size'):
            self.main_window.sp_font_size.blockSignals(True)
            self.main_window.sp_font_size.setValue(new_size)
            self.main_window.sp_font_size.blockSignals(False)

    def _on_appearance_changed(self):
        ov = self.settings.get("overlay", {})
        self.overlay_window.apply_appearance(
            font_family=ov.get("font_family", "Segoe UI"),
            font_size=ov.get("font_size", 18),
            text_color=ov.get("text_color", "#FFFFFF"),
            outline_color=ov.get("outline_color", "#05050A"),
            outline_width=ov.get("outline_width", 2),
            bg_opacity=ov.get("bg_opacity", 85),
            show_source=ov.get("show_source_text", True)
        )
        geom = ov.get("geometry", [120, 680, 1150, 230])
        self.overlay_window.setGeometry(geom[0], geom[1], geom[2], geom[3])

    def _test_api_connection(self, provider: str):
        async def _run():
            try:
                res = await self.translator.translate_full(
                    text="こんにちは！これはテストです。",
                    provider=provider,
                    src_lang="ja",
                    tgt_lang="vi",
                    bypass_fallback=True
                )
            except Exception as e:
                res = f"[Lỗi: {e}]"
                
            is_error = res.startswith("[Lỗi") or "Error" in res
            if is_error:
                title = f"Kiểm Tra API Thất Bại ({provider.upper()})"
                msg = (
                    f"❌ Không thể kết nối hoặc nhận phản hồi từ AI ({provider.upper()}).\n\n"
                    f"Chi tiết thông báo:\n{res}\n\n"
                    "Gợi ý kiểm tra:\n"
                    "1. Kiểm tra mã API Key trong tab 'Nhà Cung Cấp AI'.\n"
                    "2. Đảm bảo bạn đã bấm nút 'Lưu Cài Đặt' ở cuối trang sau khi dán key.\n"
                    "3. Kiểm tra số dư / hạn mức (quota) trên trang quản lý API của nhà cung cấp."
                )
                icon = QMessageBox.Icon.Warning
            else:
                title = f"Kết Nối API Thành Công ({provider.upper()})"
                msg = (
                    f"✅ Đã kết nối và xác thực thành công tới {provider.upper()}!\n\n"
                    f"Bản dịch thử nghiệm từ AI:\n\"{res}\""
                )
                icon = QMessageBox.Icon.Information

            QTimer.singleShot(0, lambda: QMessageBox(icon, title, msg, QMessageBox.StandardButton.Ok, self.main_window).exec())

        if hasattr(self, "_async_loop") and self._async_loop.is_running():
            asyncio.run_coroutine_threadsafe(_run(), self._async_loop)
        else:
            threading.Thread(target=lambda: asyncio.run(_run()), daemon=True).start()

    @Slot(str)
    def _handle_error(self, err_msg: str):
        logger.error(err_msg)
