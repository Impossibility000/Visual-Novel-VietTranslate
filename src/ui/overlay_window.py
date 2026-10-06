import sys
import re
import ctypes
from typing import Optional, Dict, Any, Tuple
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QSize, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QPainterPath,
    QLinearGradient, QFontMetrics, QCursor
)
from PySide6.QtWidgets import (
    QWidget, QApplication, QToolTip
)

# Windows extended window styles for Click-through
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
GWL_EXSTYLE = -20

if sys.platform == "win32":
    user32 = ctypes.windll.user32
    if hasattr(user32, "GetWindowLongPtrW"):
        _GetWindowLongPtr = user32.GetWindowLongPtrW
        _SetWindowLongPtr = user32.SetWindowLongPtrW
    else:
        _GetWindowLongPtr = user32.GetWindowLongW
        _SetWindowLongPtr = user32.SetWindowLongW
    
    _GetWindowLongPtr.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _GetWindowLongPtr.restype = ctypes.c_ssize_t
    _SetWindowLongPtr.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    _SetWindowLongPtr.restype = ctypes.c_ssize_t

class OverlayWindow(QWidget):
    """
    State-of-the-Art Floating Glassmorphism Subtitle Overlay for Visual Novels & Games.
    Features crisp 16-point anti-aliased text outline, Speaker Tag pill, Quick HUD actions,
    and Click-Through transparency.
    """
    
    geometry_changed = Signal(int, int, int, int)
    lock_toggled = Signal(bool)
    replay_tts_requested = Signal(str)
    toggle_backlog_requested = Signal()
    font_size_changed = Signal(int)

    def __init__(self, settings_dict: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.settings = settings_dict or {}
        
        # Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        
        # State
        self.source_text = ""
        self.translated_text = "AetherVN Realtime AI Translator Sẵn Sàng"
        self.speaker_name = ""
        self.is_streaming = False
        self.click_through = False
        self.is_hovered = False
        self.copied_feedback_timer = 0
        
        # Dragging & Resizing state
        self._dragging = False
        self._drag_pos = QPoint()
        self.resize_mode = None
        
        # Appearance defaults
        self.font_family = self.settings.get("font_family", "Segoe UI")
        self.font_size = self.settings.get("font_size", 19)
        self.font_weight = QFont.Weight.Bold
        self.text_color = QColor(self.settings.get("text_color", "#FFFFFF"))
        self.outline_color = QColor(self.settings.get("outline_color", "#05050A"))
        self.outline_width = self.settings.get("outline_width", 2)
        self.bg_opacity = self.settings.get("bg_opacity", 85)
        self.show_source_text = self.settings.get("show_source_text", True)
        self.source_font_size = self.settings.get("source_font_size", 13)
        self.source_text_color = QColor(self.settings.get("source_text_color", "#A0B4D8"))

        # Default size and position
        geom = self.settings.get("geometry", [150, 680, 1100, 200])
        self.setGeometry(geom[0], geom[1], geom[2], geom[3])
        self.setMinimumSize(360, 100)
        
        self.setMouseTracking(True)
        
        # Feedback timer to restore copy status
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setInterval(1200)
        self._feedback_timer.timeout.connect(self._clear_feedback)

    def _clear_feedback(self):
        self.copied_feedback_timer = 0
        self._feedback_timer.stop()
        self.update()

    def set_click_through(self, enabled: bool) -> None:
        """Toggle native Windows click-through mode safely on 64-bit Windows."""
        self.click_through = enabled
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                current_style = _GetWindowLongPtr(hwnd, GWL_EXSTYLE)
                
                if enabled:
                    new_style = current_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                else:
                    new_style = current_style & ~WS_EX_TRANSPARENT
                    
                _SetWindowLongPtr(hwnd, GWL_EXSTYLE, new_style)
            except Exception:
                pass
            
        self.lock_toggled.emit(enabled)
        self.update()

    def _extract_speaker_name(self, text: str) -> Tuple[str, str]:
        """Extract speaker tag if dialogue starts with 【Name】 or Name:"""
        if not text:
            return "", text
        m = re.match(r'^([【\[][^】\]]+[】\]]|[\w\s\u3040-\u30ff\u4e00-\u9faf]{2,15}[:：])\s*(.*)$', text)
        if m:
            speaker = m.group(1).strip()
            rest = m.group(2).strip()
            # clean brackets
            clean_speaker = speaker.strip("【】[]:：")
            return clean_speaker, rest
        return "", text

    def update_text(self, source: str, translated: str, is_streaming: bool = False) -> None:
        self.source_text = source
        self.translated_text = translated
        self.is_streaming = is_streaming
        
        # Check for speaker name tag in source or translated
        sp_src, _ = self._extract_speaker_name(source)
        sp_tgt, _ = self._extract_speaker_name(translated)
        self.speaker_name = sp_tgt or sp_src
        
        self.update()

    def append_chunk(self, chunk: str) -> None:
        if not self.is_streaming:
            self.translated_text = chunk
            self.is_streaming = True
        else:
            self.translated_text += chunk
            
        sp_src, _ = self._extract_speaker_name(self.source_text)
        sp_tgt, _ = self._extract_speaker_name(self.translated_text)
        self.speaker_name = sp_tgt or sp_src
        
        self.update()

    def set_streaming_done(self) -> None:
        self.is_streaming = False
        self.update()

    def apply_appearance(
        self,
        font_family: str,
        font_size: int,
        text_color: str,
        outline_color: str,
        outline_width: int,
        bg_opacity: int,
        show_source: bool
    ) -> None:
        self.font_family = font_family
        self.font_size = font_size
        self.text_color = QColor(text_color)
        self.outline_color = QColor(outline_color)
        self.outline_width = outline_width
        self.bg_opacity = bg_opacity
        self.show_source_text = show_source
        self.update()

    # --- Quick HUD Action Geometry & Hit Testing ---
    def _get_hud_buttons_rects(self) -> Dict[str, QRect]:
        """Compute bounding boxes for the top HUD buttons when unlocked."""
        rects = {}
        w = self.width()
        btn_w, btn_h = 28, 22
        y = 7
        
        # Right aligned buttons
        # 1. Lock/Unlock
        rects["lock"] = QRect(w - 36, y, btn_w, btn_h)
        # 2. Backlog
        rects["backlog"] = QRect(w - 68, y, btn_w, btn_h)
        # 3. TTS Replay
        rects["tts"] = QRect(w - 100, y, btn_w, btn_h)
        # 4. Copy
        rects["copy"] = QRect(w - 132, y, btn_w, btn_h)
        # 5. Font +
        rects["font_plus"] = QRect(w - 164, y, btn_w, btn_h)
        # 6. Font -
        rects["font_minus"] = QRect(w - 196, y, btn_w, btn_h)
        
        return rects

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.click_through:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            
            # Check HUD buttons first
            hud_rects = self._get_hud_buttons_rects()
            if hud_rects["lock"].contains(pos):
                self.set_click_through(True)
                return
            if hud_rects["backlog"].contains(pos):
                self.toggle_backlog_requested.emit()
                return
            if hud_rects["tts"].contains(pos):
                if self.translated_text:
                    self.replay_tts_requested.emit(self.translated_text)
                return
            if hud_rects["copy"].contains(pos):
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(f"{self.source_text}\n{self.translated_text}".strip())
                    self.copied_feedback_timer = 1
                    self._feedback_timer.start()
                    self.update()
                return
            if hud_rects["font_plus"].contains(pos):
                self.font_size = min(48, self.font_size + 1)
                self.font_size_changed.emit(self.font_size)
                self.update()
                return
            if hud_rects["font_minus"].contains(pos):
                self.font_size = max(12, self.font_size - 1)
                self.font_size_changed.emit(self.font_size)
                self.update()
                return

            margin = 20
            w, h = self.width(), self.height()
            
            if pos.x() >= w - margin and pos.y() >= h - margin:
                self.resize_mode = "resize_br"
            elif pos.x() >= w - margin:
                self.resize_mode = "resize_r"
            elif pos.y() >= h - margin:
                self.resize_mode = "resize_b"
            else:
                self.resize_mode = "move"
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
            self._dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        if self.click_through:
            return
            
        margin = 20
        w, h = self.width(), self.height()
        pos = event.position().toPoint()
        
        if not self._dragging:
            hud_rects = self._get_hud_buttons_rects()
            if any(r.contains(pos) for r in hud_rects.values()):
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            elif pos.x() >= w - margin and pos.y() >= h - margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif pos.x() >= w - margin:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif pos.y() >= h - margin:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            g_pos = event.globalPosition().toPoint()
            if self.resize_mode == "move":
                new_pos = g_pos - self._drag_pos
                self.move(new_pos)
            elif self.resize_mode == "resize_br":
                new_w = max(360, g_pos.x() - self.x())
                new_h = max(100, g_pos.y() - self.y())
                self.resize(new_w, new_h)
            elif self.resize_mode == "resize_r":
                new_w = max(360, g_pos.x() - self.x())
                self.resize(new_w, self.height())
            elif self.resize_mode == "resize_b":
                new_h = max(100, g_pos.y() - self.y())
                self.resize(self.width(), new_h)
                
            self.geometry_changed.emit(self.x(), self.y(), self.width(), self.height())
            event.accept()

    def mouseReleaseEvent(self, event):
        if not self.click_through:
            self._dragging = False
            self.resize_mode = None
            self.geometry_changed.emit(self.x(), self.y(), self.width(), self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.geometry_changed.emit(self.x(), self.y(), self.width(), self.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 1. Background Card (Glassmorphism rounded dark card)
        rect = self.rect().adjusted(2, 2, -2, -2)
        bg_alpha = int(255 * (self.bg_opacity / 100.0))
        
        # Gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(14, 18, 30, bg_alpha))
        gradient.setColorAt(0.6, QColor(9, 12, 20, bg_alpha))
        gradient.setColorAt(1.0, QColor(6, 8, 14, bg_alpha))
        
        painter.setBrush(QBrush(gradient))
        border_color = QColor(0, 210, 255, 140) if not self.click_through else QColor(16, 185, 129, 90)
        painter.setPen(QPen(border_color, 1.5))
        painter.drawRoundedRect(rect, 12, 12)
        
        # 2. Top Header Bar: Status Indicator & Speaker Pill
        y_top = 8
        header_x = rect.left() + 12
        
        # Status / Mode indicator
        if self.click_through:
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(QColor(52, 211, 153, 230))
            painter.drawText(header_x, y_top + 14, "🔒 KHÓA CLICK-THROUGH (Ctrl+F1 để mở)")
        else:
            # Status dot
            dot_color = QColor(0, 210, 255) if not self.is_streaming else QColor(245, 158, 11)
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(header_x, y_top + 4, 8, 8)
            
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            painter.setPen(QColor(160, 185, 225, 200))
            status_text = "⚡ Đang dịch..." if self.is_streaming else "🟢 Sẵn sàng | Kéo để di chuyển"
            painter.drawText(header_x + 14, y_top + 12, status_text)
            
            # Speaker Tag Pill (if present)
            if self.speaker_name:
                sp_text = f"【 {self.speaker_name} 】"
                fm_sp = QFontMetrics(QFont("Segoe UI", 9, QFont.Weight.Bold))
                sp_w = fm_sp.horizontalAdvance(sp_text) + 16
                pill_x = header_x + 200
                if pill_x + sp_w < self.width() - 210:
                    pill_rect = QRect(pill_x, y_top, sp_w, 20)
                    painter.setBrush(QBrush(QColor(0, 210, 255, 40)))
                    painter.setPen(QPen(QColor(0, 210, 255, 120), 1))
                    painter.drawRoundedRect(pill_rect, 10, 10)
                    painter.setPen(QColor(0, 230, 255))
                    painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, sp_text)

            # Draw HUD Buttons
            hud_rects = self._get_hud_buttons_rects()
            hud_items = [
                ("font_minus", "A-", "Giảm cỡ chữ", QColor(255, 255, 255, 200)),
                ("font_plus", "A+", "Tăng cỡ chữ", QColor(255, 255, 255, 200)),
                ("copy", "📋" if not self.copied_feedback_timer else "✓", "Sao chép", QColor(0, 230, 255) if self.copied_feedback_timer else QColor(255, 255, 255, 220)),
                ("tts", "🔊", "Đọc lại", QColor(0, 230, 255)),
                ("backlog", "📜", "Lịch sử thoại", QColor(255, 255, 255, 220)),
                ("lock", "🔒", "Khóa Click-Through", QColor(16, 185, 129))
            ]
            
            for key, icon_text, tip, col in hud_items:
                r = hud_rects[key]
                painter.setBrush(QBrush(QColor(255, 255, 255, 18)))
                painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
                painter.drawRoundedRect(r, 4, 4)
                
                painter.setPen(col)
                painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                painter.drawText(r, Qt.AlignmentFlag.AlignCenter, icon_text)

        # 3. Source Text (Japanese/Original Line)
        y_offset = 34
        if self.show_source_text and self.source_text:
            source_font = QFont(self.font_family, self.source_font_size)
            painter.setFont(source_font)
            painter.setPen(self.source_text_color)
            src_rect = rect.adjusted(14, y_offset, -14, 0)
            painter.drawText(src_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.source_text)
            
            fm = QFontMetrics(source_font)
            br = fm.boundingRect(src_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.source_text)
            y_offset += br.height() + 8
        else:
            y_offset += 6

        # 4. Translated Text with Cinema-Grade 16-Point Subpixel Outline
        tgt_font = QFont(self.font_family, self.font_size, self.font_weight)
        painter.setFont(tgt_font)
        
        tgt_rect = rect.adjusted(14, y_offset, -14, -10)
        text_to_draw = self.translated_text + (" ▌" if self.is_streaming else "")
        
        # Multi-angle anti-aliased outline kernel for zero halo artifacts
        outline_rad = max(1.0, float(self.outline_width))
        subpixel_kernel = [
            (-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0),
            (-0.707, -0.707), (0.707, -0.707), (-0.707, 0.707), (0.707, 0.707),
            (-0.923, -0.382), (-0.382, -0.923), (0.382, -0.923), (0.923, -0.382),
            (-0.923, 0.382), (-0.382, 0.923), (0.382, 0.923), (0.923, 0.382)
        ]
        
        # Draw soft outline
        painter.setPen(self.outline_color)
        for dx, dy in subpixel_kernel:
            painter.drawText(
                tgt_rect.translated(int(dx * outline_rad), int(dy * outline_rad)),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
                text_to_draw
            )
            
        # Draw crisp high-contrast foreground text
        painter.setPen(self.text_color)
        painter.drawText(
            tgt_rect,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
            text_to_draw
        )

        # 5. Visual Resize Grip Handle (Bottom-Right)
        if not self.click_through:
            painter.setPen(QPen(QColor(0, 210, 255, 120), 1.5))
            w, h = self.width(), self.height()
            painter.drawLine(w - 18, h - 6, w - 6, h - 18)
            painter.drawLine(w - 12, h - 6, w - 6, h - 12)
            painter.drawLine(w - 6, h - 6, w - 6, h - 6)
