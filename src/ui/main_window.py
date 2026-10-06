import os
import sys
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QMessageBox, QColorDialog, QFontComboBox,
    QFrame, QTextEdit, QScrollArea
)
from src.config.settings import AppSettings
from src.core.textractor_manager import TextractorManager

class MainWindow(QMainWindow):
    """Main Control Hub for AetherVN Realtime AI Translator."""
    
    start_requested = Signal()
    pause_requested = Signal()
    test_api_requested = Signal(str)  # provider name
    select_ocr_region_requested = Signal()
    toggle_overlay_requested = Signal()
    toggle_backlog_requested = Signal()
    appearance_changed = Signal()

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("AetherVN - Realtime AI Visual Novel Translator")
        self.resize(800, 620)
        self.setMinimumSize(700, 550)
        
        self._init_stylesheet()
        self._init_ui()
        self._load_values_from_settings()

    def _init_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0E111A;
                color: #E2E8F0;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #1E2438;
                background-color: #131722;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #0E111A;
                color: #8E9BB0;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #131722;
                color: #00D2FF;
                border-bottom: 2px solid #00D2FF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #161B29;
                color: #FFFFFF;
            }
            QGroupBox {
                border: 1px solid #1F273D;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 14px;
                font-weight: bold;
                color: #00D2FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QLineEdit, QComboBox, QSpinBox, QFontComboBox {
                background-color: #1A2030;
                border: 1px solid #2B354F;
                border-radius: 6px;
                padding: 6px 10px;
                color: #FFFFFF;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #00D2FF;
            }
            QPushButton {
                background-color: #1F263B;
                color: #E2E8F0;
                border: 1px solid #2D3754;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2A3450;
                color: #FFFFFF;
            }
            QPushButton#primary-btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B4D8, stop:1 #0077B6);
                color: #FFFFFF;
                border: none;
            }
            QPushButton#primary-btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0096C7, stop:1 #023E8A);
            }
            QPushButton#danger-btn {
                background-color: rgba(239, 68, 68, 0.2);
                color: #F87171;
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
            QPushButton#danger-btn:hover {
                background-color: rgba(239, 68, 68, 0.35);
            }
            QTableWidget {
                background-color: #161B29;
                border: 1px solid #232C42;
                gridline-color: #232C42;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #1F273D;
                color: #94A3B8;
                padding: 6px;
                font-weight: bold;
                border: none;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #232C42;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00D2FF;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # App Header Banner
        header_layout = QHBoxLayout()
        title_lbl = QLabel("✨ AetherVN Realtime AI Translator")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #00D2FF;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        self.status_badge = QLabel("🟢 SẴN SÀNG")
        self.status_badge.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #34D399; font-weight: bold; padding: 4px 10px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.4);")
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # Textractor Manager
        self.textractor_manager = TextractorManager()

        # Tabs
        self.tabs = QTabWidget()
        self.tab_trans = QWidget()
        self.tab_textractor = QWidget()
        self.tab_keys = QWidget()
        self.tab_glossary = QWidget()
        self.tab_appearance = QWidget()
        self.tab_tts_hotkeys = QWidget()
        
        self.tabs.addTab(self.tab_trans, "🎮 Dịch Thuật")
        self.tabs.addTab(self.tab_textractor, "🚀 Textractor (Hook)")
        self.tabs.addTab(self.tab_keys, "🔑 API Keys")
        self.tabs.addTab(self.tab_glossary, "📖 Từ Điển & Xưng Hô")
        self.tabs.addTab(self.tab_appearance, "🎨 Phụ Đề & Giao Diện")
        self.tabs.addTab(self.tab_tts_hotkeys, "🔊 Giọng Đọc & Phím Tắt")
        
        main_layout.addWidget(self.tabs)
        
        self._build_trans_tab()
        self._build_textractor_tab()
        self._build_keys_tab()
        self._build_glossary_tab()
        self._build_appearance_tab()
        self._build_tts_hotkeys_tab()

    def _build_trans_tab(self):
        layout = QVBoxLayout(self.tab_trans)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Top Action Bar
        action_box = QGroupBox("Điều Khiển Hoạt Động")
        action_layout = QHBoxLayout(action_box)
        
        self.btn_start_stop = QPushButton("▶ Bắt Đầu Dịch")
        self.btn_start_stop.setObjectName("primary-btn")
        self.btn_start_stop.setFixedHeight(38)
        self.btn_start_stop.clicked.connect(self._toggle_running)
        action_layout.addWidget(self.btn_start_stop)
        
        self.btn_overlay = QPushButton("📺 Hiện Khung Phụ Đề")
        self.btn_overlay.setFixedHeight(38)
        self.btn_overlay.clicked.connect(self.toggle_overlay_requested.emit)
        action_layout.addWidget(self.btn_overlay)
        
        self.btn_backlog = QPushButton("📜 Xem Lịch Sử (Backlog)")
        self.btn_backlog.setFixedHeight(38)
        self.btn_backlog.clicked.connect(self.toggle_backlog_requested.emit)
        action_layout.addWidget(self.btn_backlog)
        
        layout.addWidget(action_box)

        # Provider & Language Settings
        config_box = QGroupBox("Cấu Hình Dịch")
        form_layout = QFormLayout(config_box)
        form_layout.setSpacing(10)
        
        self.cb_provider = QComboBox()
        self.cb_provider.addItems([
            "Google Gemini (gemini-3.5-flash-lite) [Khuyên dùng - Siêu tốc & Tự nhiên]",
            "OpenAI (gpt-4o-mini)",
            "DeepSeek (deepseek-chat V3/R1)",
            "Anthropic Claude (claude-3-5-haiku)",
            "Groq (llama-3.3-70b) [Siêu tốc]",
            "OpenRouter",
            "Custom OpenAI Endpoint / Local LLM"
        ])
        self.cb_provider.currentIndexChanged.connect(self._on_provider_changed)
        form_layout.addRow("Nhà cung cấp AI:", self.cb_provider)
        
        lang_layout = QHBoxLayout()
        self.cb_src_lang = QComboBox()
        self.cb_src_lang.addItems(["Tiếng Nhật (ja)", "Tiếng Anh (en)", "Tiếng Trung (zh)", "Tiếng Hàn (ko)"])
        lang_layout.addWidget(self.cb_src_lang)
        
        arrow_lbl = QLabel(" ➔ ")
        arrow_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #00D2FF;")
        lang_layout.addWidget(arrow_lbl)
        
        self.cb_tgt_lang = QComboBox()
        self.cb_tgt_lang.addItems(["Tiếng Việt (vi)", "Tiếng Anh (en)"])
        lang_layout.addWidget(self.cb_tgt_lang)
        form_layout.addRow("Cặp ngôn ngữ:", lang_layout)

        # Capture Mechanism
        self.chk_clipboard = QCheckBox("Bắt chữ qua Clipboard / Text Hooking (Textractor / Game RAM)")
        self.chk_clipboard.setChecked(True)
        self.chk_clipboard.stateChanged.connect(self._save_trans_settings)
        form_layout.addRow("Cơ chế chính:", self.chk_clipboard)
        
        ocr_row = QHBoxLayout()
        self.chk_ocr = QCheckBox("Bật OCR quét vùng màn hình (Phụ trợ)")
        self.chk_ocr.stateChanged.connect(self._save_trans_settings)
        ocr_row.addWidget(self.chk_ocr)
        
        btn_select_ocr = QPushButton("📐 Kéo chọn vùng OCR (Ctrl+F3)")
        btn_select_ocr.clicked.connect(self.select_ocr_region_requested.emit)
        ocr_row.addWidget(btn_select_ocr)
        form_layout.addRow("Cơ chế phụ:", ocr_row)

        # Hybrid & Offline Translation Options
        mode_box = QHBoxLayout()
        self.chk_hybrid = QCheckBox("⚡ Chế độ Lai Hybrid (Dịch thô Local + AI trau chuốt) [Tiết kiệm Token]")
        self.chk_hybrid.setChecked(True)
        self.chk_hybrid.stateChanged.connect(self._save_trans_settings)
        mode_box.addWidget(self.chk_hybrid)

        self.chk_offline = QCheckBox("🛡️ Chế độ Offline 100% (0đ, 0 Token, không cần mạng)")
        self.chk_offline.stateChanged.connect(self._save_trans_settings)
        mode_box.addWidget(self.chk_offline)
        form_layout.addRow("Tùy chọn AI:", mode_box)

        layout.addWidget(config_box)

        # Realtime Activity Log preview
        log_box = QGroupBox("Câu Thoại Vừa Dịch Gần Nhất")
        log_layout = QVBoxLayout(log_box)
        self.lbl_latest_src = QLabel("Chưa có dữ liệu...")
        self.lbl_latest_src.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.lbl_latest_tgt = QLabel("Khung phụ đề đang chờ câu thoại tiếp theo...")
        self.lbl_latest_tgt.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        self.lbl_latest_tgt.setWordWrap(True)
        log_layout.addWidget(self.lbl_latest_src)
        log_layout.addWidget(self.lbl_latest_tgt)
        layout.addWidget(log_box)

    def _build_textractor_tab(self):
        layout = QVBoxLayout(self.tab_textractor)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header Status Box
        status_box = QGroupBox("Trạng Thái Tích Hợp Textractor")
        status_layout = QVBoxLayout(status_box)
        
        status_msg = QLabel("🟢 Textractor v5.2.0 (Portable) ĐÃ ĐƯỢC TÍCH HỢP SẴN trong ứng dụng.")
        status_msg.setStyleSheet("color: #34D399; font-weight: bold; font-size: 13px;")
        status_layout.addWidget(status_msg)
        
        desc_lbl = QLabel(
            "Bạn có thể khởi động Textractor trực tiếp từ các nút bên dưới mà không cần cài đặt thêm bất cứ thứ gì."
        )
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        status_layout.addWidget(desc_lbl)
        
        # Launch buttons row
        btn_row = QHBoxLayout()
        btn_launch_x86 = QPushButton("🚀 Mở Textractor (32-bit x86) [Visual Novel thông dụng]")
        btn_launch_x86.setObjectName("primary-btn")
        btn_launch_x86.setFixedHeight(40)
        btn_launch_x86.clicked.connect(lambda: self._launch_textractor("x86"))
        btn_row.addWidget(btn_launch_x86)
        
        btn_launch_x64 = QPushButton("🚀 Mở Textractor (64-bit x64) [Game mới]")
        btn_launch_x64.setFixedHeight(40)
        btn_launch_x64.clicked.connect(lambda: self._launch_textractor("x64"))
        btn_row.addWidget(btn_launch_x64)
        status_layout.addLayout(btn_row)
        layout.addWidget(status_box)

        # Step by step tutorial
        guide_box = QGroupBox("Hướng Dẫn Nhanh 3 Bước")
        guide_layout = QVBoxLayout(guide_box)
        guide_text = (
            "1️⃣  <b>Mở Game</b> và bấm nút <b>Mở Textractor (32-bit)</b> ở trên.<br>"
            "2️⃣  Trong cửa sổ Textractor, bấm nút <b>Attach to game</b> ➔ Chọn tên file <code>.exe</code> của game.<br>"
            "3️⃣  Bấm nút <b>▶ Bắt Đầu Dịch</b> trên AetherVN. Phụ đề tiếng Việt sẽ tự động xuất hiện mỗi khi có câu thoại mới!"
        )
        guide_lbl = QLabel(guide_text)
        guide_lbl.setStyleSheet("color: #E2E8F0; font-size: 13px; line-height: 1.5;")
        guide_layout.addWidget(guide_lbl)
        layout.addWidget(guide_box)

        # Process scanner
        proc_box = QGroupBox("Danh Sách Tiến Trình Game Đang Chạy Trên Máy")
        proc_layout = QVBoxLayout(proc_box)
        
        top_proc_bar = QHBoxLayout()
        top_proc_bar.addWidget(QLabel("Các ứng dụng/game có thể chọn để Attach trong Textractor:"))
        top_proc_bar.addStretch()
        
        btn_refresh_procs = QPushButton("🔄 Làm Mới Danh Sách")
        btn_refresh_procs.clicked.connect(self._refresh_running_processes)
        top_proc_bar.addWidget(btn_refresh_procs)
        proc_layout.addLayout(top_proc_bar)
        
        self.table_procs = QTableWidget()
        self.table_procs.setColumnCount(2)
        self.table_procs.setHorizontalHeaderLabels(["Tên Tiến Trình (Game .exe)", "Mã PID"])
        self.table_procs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_procs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_procs.setColumnWidth(1, 100)
        proc_layout.addWidget(self.table_procs)
        
        layout.addWidget(proc_box)
        self._refresh_running_processes()

    def _launch_textractor(self, arch: str):
        success = self.textractor_manager.launch_gui(arch)
        if success:
            QMessageBox.information(
                self, "Thông Báo",
                f"Đã khởi chạy Textractor ({arch}) thành công!\n\n"
                "Bây giờ bạn chỉ cần bấm 'Attach to game' trong Textractor và bấm 'Bắt Đầu Dịch' trên AetherVN."
            )
        else:
            QMessageBox.warning(
                self, "Lỗi",
                f"Không tìm thấy file Textractor ({arch}). Vui lòng kiểm tra thư mục tools/Textractor."
            )

    def _refresh_running_processes(self):
        procs = self.textractor_manager.list_running_processes()
        self.table_procs.setRowCount(len(procs))
        for row, item in enumerate(procs):
            self.table_procs.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.table_procs.setItem(row, 1, QTableWidgetItem(str(item["pid"])))

    def _build_keys_tab(self):
        layout = QVBoxLayout(self.tab_keys)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        # Helper Banner for Gemini API Key
        help_box = QGroupBox("Hướng Dẫn Lấy Google Gemini API Key (Miễn Phí)")
        help_layout = QHBoxLayout(help_box)
        
        help_text = QLabel("💡 Gemini API Key là chuỗi ký tự được tạo tại Google AI Studio (bắt đầu bằng <b>AIzaSy...</b> hoặc <b>AQ...</b>).")
        help_text.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        help_layout.addWidget(help_text)
        
        import webbrowser
        btn_open_aistudio = QPushButton("🔗 Mở Trang Lấy Key (Google AI Studio)")
        btn_open_aistudio.setObjectName("primary-btn")
        btn_open_aistudio.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        help_layout.addWidget(btn_open_aistudio)
        
        layout.addWidget(help_box)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        form_layout.setSpacing(12)
        
        self.key_inputs = {}
        providers = [
            ("gemini", "Google Gemini API Key:"),
            ("openai", "OpenAI API Key:"),
            ("deepseek", "DeepSeek API Key:"),
            ("claude", "Anthropic Claude API Key:"),
            ("groq", "Groq API Key:"),
            ("openrouter", "OpenRouter API Key:"),
            ("custom", "Custom / Local API Key:")
        ]
        
        for p_id, p_label in providers:
            row = QHBoxLayout()
            le = QLineEdit()
            le.setEchoMode(QLineEdit.EchoMode.Password)
            le.setPlaceholderText(f"Nhập API key cho {p_id}...")
            le.textChanged.connect(self._save_keys)
            self.key_inputs[p_id] = le
            row.addWidget(le)
            
            toggle_eye = QPushButton("👁")
            toggle_eye.setFixedWidth(36)
            toggle_eye.clicked.connect(lambda checked=False, target=le: self._toggle_echo_mode(target))
            row.addWidget(toggle_eye)
            
            test_btn = QPushButton("Test")
            test_btn.setFixedWidth(60)
            test_btn.clicked.connect(lambda checked=False, pid=p_id: self.test_api_requested.emit(pid))
            row.addWidget(test_btn)
            
            form_layout.addRow(p_label, row)

        # Custom Endpoint URL
        self.le_custom_url = QLineEdit()
        self.le_custom_url.setPlaceholderText("http://localhost:11434/v1")
        self.le_custom_url.textChanged.connect(self._save_keys)
        form_layout.addRow("Custom Base URL:", self.le_custom_url)

        # System Prompt customization
        prompt_header_layout = QHBoxLayout()
        prompt_header_layout.addWidget(QLabel("System Prompt AI (Để trống sẽ dùng Prompt chuyên gia mặc định):"))
        btn_reset_prompt = QPushButton("🔄 Khôi phục Prompt chuẩn")
        btn_reset_prompt.setFixedWidth(180)
        btn_reset_prompt.clicked.connect(self._reset_system_prompt_to_default)
        prompt_header_layout.addWidget(btn_reset_prompt)
        form_layout.addRow(prompt_header_layout)
        
        self.te_system_prompt = QTextEdit()
        self.te_system_prompt.setMaximumHeight(80)
        self.te_system_prompt.textChanged.connect(self._save_keys)
        form_layout.addRow(self.te_system_prompt)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _build_glossary_tab(self):
        layout = QVBoxLayout(self.tab_glossary)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        info_lbl = QLabel("Bảng từ điển giúp AI dịch đúng tên nhân vật, danh xưng (Senpai -> Tiền bối, Ore -> Tôi, Anata -> Anh...)")
        info_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(info_lbl)
        
        # Add new rule bar
        add_layout = QHBoxLayout()
        self.le_orig = QLineEdit()
        self.le_orig.setPlaceholderText("Từ gốc (VD: 先輩, 桜, 俺)")
        add_layout.addWidget(self.le_orig)
        
        self.le_trans = QLineEdit()
        self.le_trans.setPlaceholderText("Bản dịch / Xưng hô (VD: Tiền bối, Sakura, Tôi)")
        add_layout.addWidget(self.le_trans)
        
        btn_add = QPushButton("➕ Thêm Quy Tắc")
        btn_add.setObjectName("primary-btn")
        btn_add.clicked.connect(self._add_glossary_item)
        add_layout.addWidget(btn_add)
        layout.addLayout(add_layout)
        
        # Glossary Table
        self.table_glossary = QTableWidget()
        self.table_glossary.setColumnCount(3)
        self.table_glossary.setHorizontalHeaderLabels(["Từ Gốc", "Bản Dịch / Xưng Hô", "Thao Tác"])
        self.table_glossary.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_glossary.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_glossary.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_glossary.setColumnWidth(2, 90)
        layout.addWidget(self.table_glossary)

    def _build_appearance_tab(self):
        layout = QVBoxLayout(self.tab_appearance)
        layout.setContentsMargins(16, 16, 16, 16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        form_layout.setSpacing(12)
        
        # Font family
        self.fc_font = QFontComboBox()
        self.fc_font.currentFontChanged.connect(self._save_appearance)
        form_layout.addRow("Font Chữ Phụ Đề:", self.fc_font)
        
        # Font size
        self.sp_font_size = QSpinBox()
        self.sp_font_size.setRange(12, 48)
        self.sp_font_size.setValue(18)
        self.sp_font_size.valueChanged.connect(self._save_appearance)
        form_layout.addRow("Cỡ Chữ Phụ Đề (px):", self.sp_font_size)
        
        # Text Color
        col_row = QHBoxLayout()
        self.btn_text_color = QPushButton("Chọn Màu Chữ")
        self.btn_text_color.clicked.connect(self._pick_text_color)
        col_row.addWidget(self.btn_text_color)
        
        self.btn_outline_color = QPushButton("Chọn Màu Viền")
        self.btn_outline_color.clicked.connect(self._pick_outline_color)
        col_row.addWidget(self.btn_outline_color)
        form_layout.addRow("Màu Sắc:", col_row)
        
        # Outline Width
        self.sp_outline_width = QSpinBox()
        self.sp_outline_width.setRange(0, 6)
        self.sp_outline_width.setValue(2)
        self.sp_outline_width.valueChanged.connect(self._save_appearance)
        form_layout.addRow("Độ Dày Viền Chữ (px):", self.sp_outline_width)
        
        # Background Opacity
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sl_opacity.setRange(0, 100)
        self.sl_opacity.setValue(85)
        self.sl_opacity.valueChanged.connect(self._save_appearance)
        form_layout.addRow("Độ Mờ Đục Nền (%):", self.sl_opacity)
        
        # Show Source Text
        self.chk_show_source = QCheckBox("Hiển thị dòng thoại gốc tiếng Nhật/Anh phía trên")
        self.chk_show_source.setChecked(True)
        self.chk_show_source.stateChanged.connect(self._save_appearance)
        form_layout.addRow("Câu Gốc:", self.chk_show_source)

        # Overlay Dimensions & Presets
        dim_box = QGroupBox("Kích Thước Khung Phụ Đề (Có thể kéo chuột trực tiếp ở góc khung)")
        dim_layout = QFormLayout(dim_box)
        
        self.sp_overlay_width = QSpinBox()
        self.sp_overlay_width.setRange(350, 3840)
        self.sp_overlay_width.setSingleStep(50)
        self.sp_overlay_width.setValue(1150)
        self.sp_overlay_width.valueChanged.connect(self._save_appearance)
        dim_layout.addRow("Chiều Rộng Khung (px):", self.sp_overlay_width)
        
        self.sp_overlay_height = QSpinBox()
        self.sp_overlay_height.setRange(90, 2160)
        self.sp_overlay_height.setSingleStep(20)
        self.sp_overlay_height.setValue(230)
        self.sp_overlay_height.valueChanged.connect(self._save_appearance)
        dim_layout.addRow("Chiều Cao Khung (px):", self.sp_overlay_height)

        preset_row = QHBoxLayout()
        btn_preset_compact = QPushButton("📐 Gọn (900x160)")
        btn_preset_compact.clicked.connect(lambda: self._set_overlay_size(900, 160))
        preset_row.addWidget(btn_preset_compact)

        btn_preset_standard = QPushButton("🖥 Rộng Chuẩn VN (1150x230)")
        btn_preset_standard.setObjectName("primary-btn")
        btn_preset_standard.clicked.connect(lambda: self._set_overlay_size(1150, 230))
        preset_row.addWidget(btn_preset_standard)

        btn_preset_wide = QPushButton("🎬 Siêu Rộng (1450x280)")
        btn_preset_wide.clicked.connect(lambda: self._set_overlay_size(1450, 280))
        preset_row.addWidget(btn_preset_wide)
        dim_layout.addRow("Kích Thước Nhanh:", preset_row)

        form_layout.addRow(dim_box)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _build_tts_hotkeys_tab(self):
        layout = QVBoxLayout(self.tab_tts_hotkeys)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # TTS Box
        tts_box = QGroupBox("Cấu Hình Giọng Đọc (Microsoft Edge-TTS)")
        tts_layout = QFormLayout(tts_box)
        
        self.chk_auto_tts = QCheckBox("Tự động đọc giọng sau khi dịch xong câu thoại")
        self.chk_auto_tts.stateChanged.connect(self._save_tts)
        tts_layout.addRow("Tự Động Đọc:", self.chk_auto_tts)
        
        self.cb_tts_voice = QComboBox()
        from src.core.tts_player import TTSPlayer
        for k, v in TTSPlayer.VOICE_LIST.items():
            self.cb_tts_voice.addItem(v, k)
        self.cb_tts_voice.currentIndexChanged.connect(self._save_tts)
        tts_layout.addRow("Giọng Đọc:", self.cb_tts_voice)
        
        layout.addWidget(tts_box)

        # Hotkeys Box
        hk_box = QGroupBox("Danh Sách Phím Tắt Toàn Cục (Global Hotkeys)")
        hk_layout = QVBoxLayout(hk_box)
        
        hotkeys_info = [
            ("Ctrl + F1", "Bật / Tắt chế độ Click-Through (chuột xuyên qua phụ đề)"),
            ("Ctrl + F2", "Tạm dừng / Tiếp tục tiến trình dịch"),
            ("Ctrl + F3", "Kéo chọn vùng màn hình OCR mới"),
            ("Ctrl + F4", "Ẩn / Hiện nhanh khung phụ đề"),
            ("Ctrl + F5", "Đọc lại câu thoại vừa dịch bằng giọng TTS")
        ]
        
        for key, desc in hotkeys_info:
            row = QHBoxLayout()
            key_badge = QLabel(key)
            key_badge.setStyleSheet("background: #1F273D; color: #00D2FF; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-family: monospace;")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #CBD5E1;")
            row.addWidget(key_badge)
            row.addWidget(desc_lbl)
            row.addStretch()
            hk_layout.addLayout(row)
            
        layout.addWidget(hk_box)
        layout.addStretch()

    def _toggle_echo_mode(self, line_edit: QLineEdit):
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _toggle_running(self):
        if self.btn_start_stop.text().startswith("▶"):
            self.start_requested.emit()
            self.btn_start_stop.setText("⏸ Tạm Dừng Dịch")
            self.btn_start_stop.setObjectName("danger-btn")
            self.btn_start_stop.setStyle(self.btn_start_stop.style())
            self.status_badge.setText("🟢 ĐANG HOẠT ĐỘNG")
            self.status_badge.setStyleSheet("background: rgba(16, 185, 129, 0.2); color: #34D399; font-weight: bold; padding: 4px 10px; border-radius: 12px;")
        else:
            self.pause_requested.emit()
            self.btn_start_stop.setText("▶ Bắt Đầu Dịch")
            self.btn_start_stop.setObjectName("primary-btn")
            self.btn_start_stop.setStyle(self.btn_start_stop.style())
            self.status_badge.setText("⏸ TẠM DỪNG")
            self.status_badge.setStyleSheet("background: rgba(245, 158, 11, 0.2); color: #FBBF24; font-weight: bold; padding: 4px 10px; border-radius: 12px;")

    def _on_provider_changed(self, idx: int):
        providers = ["gemini", "openai", "deepseek", "claude", "groq", "openrouter", "custom"]
        if idx < len(providers):
            self.settings.set("selected_provider", providers[idx])
            self.settings.save()

    def _save_trans_settings(self):
        self.settings.set("clipboard", {"enabled": self.chk_clipboard.isChecked(), "debounce_ms": 250})
        ocr_cfg = self.settings.get("ocr", {})
        ocr_cfg["enabled"] = self.chk_ocr.isChecked()
        self.settings.set("ocr", ocr_cfg)
        self.settings.set("hybrid_mode", self.chk_hybrid.isChecked())
        self.settings.set("offline_only", self.chk_offline.isChecked())
        self.settings.save()

    def _save_keys(self):
        for pid, le in self.key_inputs.items():
            self.settings.set_provider_key(pid, le.text().strip())
        
        custom_cfg = self.settings.get_provider_config("custom")
        custom_cfg["base_url"] = self.le_custom_url.text().strip()
        self.settings.set("system_prompt", self.te_system_prompt.toPlainText().strip())
        self.settings.save()

    def _reset_system_prompt_to_default(self):
        from src.config.settings import DEFAULT_SETTINGS
        default_p = DEFAULT_SETTINGS.get("system_prompt", "")
        self.te_system_prompt.setText(default_p)
        self.settings.set("system_prompt", default_p)
        self.settings.save()
        QMessageBox.information(self, "Thông Báo", "Đã khôi phục System Prompt tối ưu mặc định thành công!")

    def _pick_text_color(self):
        col = QColorDialog.getColor(initial=QColor(self.settings.get("overlay", {}).get("text_color", "#FFFFFF")), parent=self)
        if col.isValid():
            overlay_cfg = self.settings.get("overlay", {})
            overlay_cfg["text_color"] = col.name()
            self.settings.set("overlay", overlay_cfg)
            self.settings.save()

    def _pick_outline_color(self):
        col = QColorDialog.getColor(initial=QColor(self.settings.get("overlay", {}).get("outline_color", "#05050A")), parent=self)
        if col.isValid():
            overlay_cfg = self.settings.get("overlay", {})
            overlay_cfg["outline_color"] = col.name()
            self.settings.set("overlay", overlay_cfg)
            self.settings.save()

    def _save_appearance(self):
        overlay_cfg = self.settings.get("overlay", {})
        overlay_cfg["font_family"] = self.fc_font.currentFont().family()
        overlay_cfg["font_size"] = self.sp_font_size.value()
        overlay_cfg["outline_width"] = self.sp_outline_width.value()
        overlay_cfg["bg_opacity"] = self.sl_opacity.value()
        overlay_cfg["show_source_text"] = self.chk_show_source.isChecked()
        
        geom = overlay_cfg.get("geometry", [120, 680, 1150, 230])
        if hasattr(self, 'sp_overlay_width') and hasattr(self, 'sp_overlay_height'):
            geom[2] = self.sp_overlay_width.value()
            geom[3] = self.sp_overlay_height.value()
        overlay_cfg["geometry"] = geom
        
        self.settings.set("overlay", overlay_cfg)
        self.settings.save()
        self.appearance_changed.emit()

    def _set_overlay_size(self, width: int, height: int):
        self.sp_overlay_width.setValue(width)
        self.sp_overlay_height.setValue(height)
        self._save_appearance()

    def _save_tts(self):
        tts_cfg = self.settings.get("tts", {})
        tts_cfg["enabled"] = self.chk_auto_tts.isChecked()
        tts_cfg["voice"] = self.cb_tts_voice.currentData()
        self.settings.set("tts", tts_cfg)
        self.settings.save()

    def _add_glossary_item(self):
        orig = self.le_orig.text().strip()
        trans = self.le_trans.text().strip()
        if not orig or not trans:
            return
        self.settings.set_glossary_entry(orig, trans)
        self.settings.save()
        self.le_orig.clear()
        self.le_trans.clear()
        self._refresh_glossary_table()

    def _refresh_glossary_table(self):
        rules = self.settings.get("glossary", {})
        self.table_glossary.setRowCount(len(rules))
        for row, (orig, trans) in enumerate(rules.items()):
            self.table_glossary.setItem(row, 0, QTableWidgetItem(orig))
            self.table_glossary.setItem(row, 1, QTableWidgetItem(trans))
            
            del_btn = QPushButton("Xóa")
            del_btn.setStyleSheet("background: rgba(239, 68, 68, 0.2); color: #F87171; border: none; border-radius: 4px;")
            del_btn.clicked.connect(lambda ch=False, k=orig: self._delete_glossary_item(k))
            self.table_glossary.setCellWidget(row, 2, del_btn)

    def _delete_glossary_item(self, key: str):
        self.settings.remove_glossary_entry(key)
        self.settings.save()
        self._refresh_glossary_table()

    def _load_values_from_settings(self):
        # Provider
        prov = self.settings.get("selected_provider", "gemini")
        providers = ["gemini", "openai", "deepseek", "claude", "groq", "openrouter", "custom"]
        if prov in providers:
            self.cb_provider.setCurrentIndex(providers.index(prov))
            
        # Translation Options
        self.chk_clipboard.setChecked(self.settings.get("clipboard", {}).get("enabled", True))
        self.chk_ocr.setChecked(self.settings.get("ocr", {}).get("enabled", False))
        self.chk_hybrid.setChecked(self.settings.get("hybrid_mode", True))
        self.chk_offline.setChecked(self.settings.get("offline_only", False))

        # Keys
        for pid, le in self.key_inputs.items():
            le.setText(self.settings.get_provider_key(pid))
        self.le_custom_url.setText(self.settings.get_provider_config("custom").get("base_url", ""))
        self.te_system_prompt.setText(self.settings.get("system_prompt", ""))
        
        # Appearance
        ov = self.settings.get("overlay", {})
        self.fc_font.setCurrentFont(QFont(ov.get("font_family", "Segoe UI")))
        self.sp_font_size.setValue(ov.get("font_size", 18))
        self.sp_outline_width.setValue(ov.get("outline_width", 2))
        self.sl_opacity.setValue(ov.get("bg_opacity", 85))
        self.chk_show_source.setChecked(ov.get("show_source_text", True))
        
        geom = ov.get("geometry", [120, 680, 1150, 230])
        if hasattr(self, 'sp_overlay_width') and hasattr(self, 'sp_overlay_height'):
            self.sp_overlay_width.setValue(geom[2])
            self.sp_overlay_height.setValue(geom[3])
        
        # TTS
        tts = self.settings.get("tts", {})
        self.chk_auto_tts.setChecked(tts.get("enabled", False))
        voice = tts.get("voice", "vi-VN-HoaiMyNeural")
        for i in range(self.cb_tts_voice.count()):
            if self.cb_tts_voice.itemData(i) == voice:
                self.cb_tts_voice.setCurrentIndex(i)
                break
                
        # Glossary
        self._refresh_glossary_table()

    def update_latest_dialogue(self, source: str, translated: str):
        self.lbl_latest_src.setText(source)
        self.lbl_latest_tgt.setText(translated)
