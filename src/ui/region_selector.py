import sys
from typing import Optional, Tuple
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor
from PySide6.QtWidgets import QDialog, QApplication

class RegionSelectorDialog(QDialog):
    """Fullscreen semi-transparent overlay to drag & select a screen region for OCR."""
    
    region_selected = Signal(int, int, int, int)  # x, y, width, height

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        
        self._start_pos: Optional[QPoint] = None
        self._current_pos: Optional[QPoint] = None
        self._is_selecting = False
        
        # Cover entire virtual desktop
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.virtualGeometry())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint()
            self._current_pos = self._start_pos
            self._is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            self._current_pos = event.globalPosition().toPoint()
            
            rect = self._get_normalized_rect()
            if rect.width() > 10 and rect.height() > 10:
                self.region_selected.emit(rect.x(), rect.y(), rect.width(), rect.height())
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def _get_normalized_rect(self) -> QRect:
        if not self._start_pos or not self._current_pos:
            return QRect()
        x1 = min(self._start_pos.x(), self._current_pos.x())
        y1 = min(self._start_pos.y(), self._current_pos.y())
        x2 = max(self._start_pos.x(), self._current_pos.x())
        y2 = max(self._start_pos.y(), self._current_pos.y())
        return QRect(x1, y1, x2 - x1, y2 - y1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw dark semi-transparent backdrop
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        
        if self._start_pos and self._current_pos:
            rect = self._get_normalized_rect()
            # Clear selected area
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # Draw glowing cyan border
            pen = QPen(QColor(0, 220, 255, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # Draw size badge
            badge_text = f"{rect.width()} x {rect.height()} px"
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect.x() + 8, rect.y() - 8 if rect.y() > 30 else rect.y() + 20, badge_text)
        else:
            # Draw helper tip
            painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255, 220))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Kéo chuột để chọn vùng nhận diện OCR cho game\n(Nhấn ESC để hủy)"
            )
