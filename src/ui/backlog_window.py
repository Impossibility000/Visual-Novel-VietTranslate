import json
import time
from typing import Callable, Optional, List, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QFileDialog, QMessageBox, QFrame, QApplication
)

class DialogueItemWidget(QFrame):
    """Custom widget for rendering a single dialogue history entry."""
    
    replay_requested = Signal(str)  # text to play

    def __init__(self, timestamp: str, source: str, translated: str, parent=None):
        super().__init__(parent)
        self.timestamp = timestamp
        self.source = source
        self.translated = translated
        
        self.setStyleSheet("""
            DialogueItemWidget {
                background: rgba(30, 34, 48, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px;
                margin-bottom: 4px;
            }
            DialogueItemWidget:hover {
                background: rgba(40, 46, 64, 0.9);
                border: 1px solid rgba(0, 220, 255, 0.3);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Header row: timestamp & buttons
        header_layout = QHBoxLayout()
        time_lbl = QLabel(timestamp)
        time_lbl.setStyleSheet("color: #7A859E; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(time_lbl)
        header_layout.addStretch()
        
        # Copy button
        copy_btn = QPushButton("📋 Sao chép")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #C0C8E0;
                border: none;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
        """)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        header_layout.addWidget(copy_btn)
        
        # Replay TTS button
        tts_btn = QPushButton("🔊 Đọc lại")
        tts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tts_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 200, 255, 0.15);
                color: #00E5FF;
                border: none;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 200, 255, 0.3);
            }
        """)
        tts_btn.clicked.connect(lambda: self.replay_requested.emit(self.translated))
        header_layout.addWidget(tts_btn)
        
        layout.addLayout(header_layout)
        
        # Source text
        if source:
            src_lbl = QLabel(source)
            src_lbl.setWordWrap(True)
            src_lbl.setStyleSheet("color: #98A2B8; font-size: 13px;")
            layout.addWidget(src_lbl)
        
        # Translated text
        tgt_lbl = QLabel(translated)
        tgt_lbl.setWordWrap(True)
        tgt_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        layout.addWidget(tgt_lbl)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(f"{self.source}\n{self.translated}")

class BacklogWindow(QWidget):
    """Dialogue History / Backlog window with search, TTS replay, and export."""
    
    tts_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lịch Sử Hội Thoại (Dialogue Backlog)")
        self.resize(650, 500)
        self._history_entries: List[Dict[str, str]] = []
        
        self.setStyleSheet("""
            QWidget {
                background-color: #12141D;
                color: #E2E8F0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #1A1D2A;
                border: 1px solid #2E364F;
                border-radius: 6px;
                padding: 6px 12px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00D2FF;
            }
            QListWidget {
                background-color: #161824;
                border: 1px solid #24293E;
                border-radius: 8px;
                padding: 4px;
            }
            QPushButton.action-btn {
                background-color: #1E2336;
                color: #C0CCE6;
                border: 1px solid #333B58;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton.action-btn:hover {
                background-color: #293049;
                color: #FFFFFF;
            }
            QPushButton.danger-btn {
                background-color: rgba(239, 68, 68, 0.15);
                color: #F87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton.danger-btn:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)
        
        # Search and controls top row
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm trong lịch sử thoại...")
        self.search_input.textChanged.connect(self._filter_history)
        top_layout.addWidget(self.search_input)
        
        clear_btn = QPushButton("Xóa tất cả")
        clear_btn.setProperty("class", "danger-btn")
        clear_btn.clicked.connect(self.clear_history)
        top_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("💾 Xuất file")
        export_btn.setProperty("class", "action-btn")
        export_btn.clicked.connect(self.export_history)
        top_layout.addWidget(export_btn)
        
        main_layout.addLayout(top_layout)
        
        # History List
        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        main_layout.addWidget(self.list_widget)

    def add_entry(self, source: str, translated: str) -> None:
        """Add a newly translated line to the backlog."""
        if not translated:
            return
        
        timestamp = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "source": source,
            "translated": translated
        }
        self._history_entries.append(entry)
        self._append_entry_widget(entry)

    def _append_entry_widget(self, entry: Dict[str, str]) -> None:
        widget = DialogueItemWidget(entry["timestamp"], entry["source"], entry["translated"])
        widget.replay_requested.connect(self.tts_requested.emit)
        
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self.list_widget.scrollToBottom()

    def _filter_history(self, keyword: str) -> None:
        kw = keyword.lower().strip()
        self.list_widget.clear()
        for entry in self._history_entries:
            if not kw or kw in entry["source"].lower() or kw in entry["translated"].lower():
                self._append_entry_widget(entry)

    def clear_history(self) -> None:
        if not self._history_entries:
            return
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc chắn muốn xóa toàn bộ lịch sử thoại?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._history_entries.clear()
            self.list_widget.clear()

    def export_history(self) -> None:
        if not self._history_entries:
            QMessageBox.information(self, "Thông báo", "Lịch sử hội thoại đang trống.")
            return
        
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Xuất lịch sử hội thoại", "dialogue_history.txt",
            "Text Files (*.txt);;JSON Files (*.json)"
        )
        if not path:
            return
        
        try:
            if path.endswith(".json") or "json" in selected_filter.lower():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._history_entries, f, indent=2, ensure_ascii=False)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for e in self._history_entries:
                        f.write(f"[{e['timestamp']}]\n{e['source']}\n-> {e['translated']}\n\n")
            QMessageBox.information(self, "Thành công", f"Đã xuất {len(self._history_entries)} câu thoại ra file.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file: {e}")
