import os
import sys
import webbrowser
from typing import Optional, Dict, Any, Tuple
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QPalette
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox,
    QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QColorDialog, QFontComboBox, QFrame, QTextEdit,
    QScrollArea, QSizePolicy
)
from src.config.settings import AppSettings
from src.core.textractor_manager import TextractorManager


class MainWindow(QMainWindow):
    """
    State-of-the-Art Windows 11 Native Fluent UI Control Center for AetherVN.
    Features WinUI 3 Navigation View, Responsive Settings Card architecture,
    and balanced responsive layout across both small and maximized screen sizes.
    """
    
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
        self.setWindowTitle("AetherVN - Visual Novel Realtime AI Translator")
        self.resize(1000, 700)
        self.setMinimumSize(840, 580)
        
        self.textractor_manager = TextractorManager()
        self.nav_buttons = []
        self.key_inputs = {}
        
        self._init_stylesheet()
        self._init_ui()
        self._load_values_from_settings()

    def _init_stylesheet(self):
        self.setStyleSheet("""
            /* Base Window & Global Fonts */
            QMainWindow, QWidget {
                background-color: #202020;
                color: #FFFFFF;
                font-family: 'Segoe UI', 'Segoe UI Variable Text', 'Segoe UI Emoji', system-ui, sans-serif;
            }
            
            /* Left Sidebar Navigation Rail */
            #sidebar {
                background-color: #181818;
                border-right: 1px solid #282828;
            }
            #sidebar QLabel {
                background-color: transparent;
            }
            
            /* Navigation Items */
            QPushButton[nav="true"], QPushButton#nav_btn {
                background-color: transparent;
                color: #B5B5B5;
                border: none;
                border-radius: 6px;
                padding: 9px 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton[nav="true"]:hover, QPushButton#nav_btn:hover {
                background-color: #262626;
                color: #FFFFFF;
            }
            QPushButton[nav="true"][active="true"], QPushButton#nav_btn[active="true"] {
                background-color: #2B2B2B;
                color: #60CDFF;
                font-weight: 600;
                border-left: 3px solid #60CDFF;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }
            
            /* Content Area & Scroll */
            QScrollArea, #content_scroll {
                background-color: #202020;
                border: none;
            }
            #content_widget, #inner_container {
                background-color: transparent;
            }
            
            /* WinUI 3 Setting Cards */
            QFrame#setting_card, QFrame[card="true"] {
                background-color: #282828;
                border: 1px solid #363636;
                border-radius: 8px;
            }
            QFrame#setting_card:hover, QFrame[card="true"]:hover {
                border: 1px solid #484848;
            }
            QFrame#setting_card QLabel, QFrame[card="true"] QLabel {
                background-color: transparent;
            }
            
            /* Inputs & Dropdowns */
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #1F1F1F;
                border: 1px solid #3C3C3C;
                border-bottom: 2px solid #585858;
                border-radius: 5px;
                padding: 5px 9px;
                color: #FFFFFF;
                font-size: 13px;
                min-height: 22px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 1px solid #60CDFF;
                border-bottom: 2px solid #60CDFF;
            }
            QComboBox QAbstractItemView {
                background-color: #2B2B2B;
                border: 1px solid #3C3C3C;
                selection-background-color: #0078D4;
                selection-color: #FFFFFF;
                border-radius: 6px;
                padding: 4px;
                color: #FFFFFF;
            }
            
            /* Primary Action Button (Windows 11 Accent Blue) */
            QPushButton#primary-btn {
                background-color: #0078D4;
                color: #FFFFFF;
                border: 1px solid #1084D9;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#primary-btn:hover {
                background-color: #1886D9;
            }
            QPushButton#primary-btn:pressed {
                background-color: #006CBE;
            }
            
            /* Secondary Standard Buttons */
            QPushButton {
                background-color: #2E2E2E;
                color: #E0E0E0;
                border: 1px solid #3D3D3D;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #383838;
                border-color: #4C4C4C;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #242424;
            }
            
            /* Danger Button */
            QPushButton#danger-btn {
                background-color: #C42B1C;
                color: #FFFFFF;
                border: 1px solid #D13438;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#danger-btn:hover {
                background-color: #D13438;
            }
            
            /* Checkbox */
            QCheckBox {
                color: #E0E0E0;
                font-size: 13px;
                spacing: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                border-radius: 4px;
                border: 1px solid #585858;
                background-color: #222222;
            }
            QCheckBox::indicator:hover {
                border-color: #7A7A7A;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D4;
                border-color: #0078D4;
            }
            
            /* Tables */
            QTableWidget {
                background-color: #222222;
                border: 1px solid #343434;
                border-radius: 6px;
                gridline-color: #2C2C2C;
                color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #292929;
                color: #A0A0A0;
                border: none;
                border-bottom: 1px solid #363636;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 12px;
            }
            
            /* Sliders */
            QSlider {
                background-color: transparent;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #383838;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #60CDFF;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            
            /* Smooth Fluent Scrollbars - Zero GDI Halftone */
            QScrollBar:vertical {
                background-color: #202020;
                width: 9px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3C3C3C;
                min-height: 28px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4E4E4E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
                background: transparent;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: #202020;
                border: none;
            }
            QScrollBar:horizontal {
                height: 0px;
                border: none;
            }
            #scroll_corner, QAbstractScrollArea::corner {
                background-color: #202020;
                border: none;
            }
        """)

    def _init_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # 1. Left Sidebar Navigation Rail (Balanced 230px width)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 18, 10, 18)
        sidebar_layout.setSpacing(5)
        
        # App Title Header
        title_box = QVBoxLayout()
        title_box.setContentsMargins(8, 0, 8, 14)
        title_box.setSpacing(2)
        
        app_name = QLabel("AetherVN")
        app_name.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF;")
        title_box.addWidget(app_name)
        
        app_desc = QLabel("Visual Novel AI Translator")
        app_desc.setStyleSheet("font-size: 11px; color: #888888;")
        title_box.addWidget(app_desc)
        sidebar_layout.addLayout(title_box)
        
        # Navigation Items (Using double ampersand && for literal & in QPushButton)
        nav_items = [
            ("⚡", "Dịch Thuật"),
            ("🔗", "Textractor Hook"),
            ("🔑", "Nhà Cung Cấp AI"),
            ("📚", "Từ Điển && Xưng Hô"),
            ("🎨", "Giao Diện Phụ Đề"),
            ("🔊", "Giọng Đọc && Phím Tắt")
        ]
        
        for idx, (icon, text) in enumerate(nav_items):
            btn = QPushButton(f"  {icon}   {text}")
            btn.setObjectName("nav_btn")
            btn.setProperty("nav", "true")
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch=False, index=idx: self._switch_page(index))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)
            
        sidebar_layout.addStretch()
        
        # Status Card in Bottom Sidebar
        status_box = QFrame()
        status_box.setStyleSheet("background: #232323; border: 1px solid #323232; border-radius: 8px; padding: 10px;")
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setContentsMargins(8, 6, 8, 6)
        sb_layout.setSpacing(3)
        
        st_title = QLabel("Trạng thái tiến trình:")
        st_title.setStyleSheet("font-size: 11px; color: #888888;")
        sb_layout.addWidget(st_title)
        
        self.status_badge = QLabel("🟢 SẴN SÀNG")
        self.status_badge.setStyleSheet("color: #60CDFF; font-weight: 600; font-size: 12px;")
        sb_layout.addWidget(self.status_badge)
        sidebar_layout.addWidget(status_box)
        
        root_layout.addWidget(sidebar)
        
        # 2. Right Content Area (Centered Responsive Layout on wide screens)
        scroll = QScrollArea()
        scroll.setObjectName("content_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        vp_pal = scroll.viewport().palette()
        vp_pal.setColor(QPalette.ColorRole.Window, QColor("#202020"))
        vp_pal.setColor(QPalette.ColorRole.Base, QColor("#202020"))
        scroll.viewport().setPalette(vp_pal)
        scroll.viewport().setAutoFillBackground(True)
        
        corner = QWidget()
        corner.setObjectName("scroll_corner")
        scroll.setCornerWidget(corner)
        
        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        content_outer_h = QHBoxLayout(content_widget)
        content_outer_h.setContentsMargins(22, 18, 22, 22)
        content_outer_h.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        # Inner Responsive Container: max-width 960px ensures balanced proportions when maximized
        inner_container = QWidget()
        inner_container.setObjectName("inner_container")
        inner_container.setMaximumWidth(960)
        inner_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.content_layout = QVBoxLayout(inner_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)
        
        self.pages_stack = QStackedWidget()
        self._build_trans_page()
        self._build_textractor_page()
        self._build_keys_page()
        self._build_glossary_page()
        self._build_appearance_page()
        self._build_tts_hotkeys_page()
        
        self.content_layout.addWidget(self.pages_stack)
        content_outer_h.addWidget(inner_container)
        
        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll, stretch=1)
        
        self._switch_page(0)

    def _switch_page(self, index: int):
        self.pages_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _create_card(self, title: str = "", subtitle: str = "") -> Tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("setting_card")
        card.setProperty("card", "true")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(12)
        
        if title:
            header_col = QVBoxLayout()
            header_col.setSpacing(2)
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #FFFFFF; background: transparent;")
            header_col.addWidget(title_lbl)
            if subtitle:
                sub_lbl = QLabel(subtitle)
                sub_lbl.setStyleSheet("font-size: 12px; color: #9A9A9A; background: transparent;")
                sub_lbl.setWordWrap(True)
                header_col.addWidget(sub_lbl)
            card_layout.addLayout(header_col)
            
        return card, card_layout

    def _create_setting_row(self, title: str, subtitle: str, control_widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 3, 0, 3)
        row.setSpacing(14)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #E8E8E8; background: transparent;")
        t_lbl.setWordWrap(True)
        text_col.addWidget(t_lbl)
        
        if subtitle:
            s_lbl = QLabel(subtitle)
            s_lbl.setStyleSheet("font-size: 11px; color: #8A8A8A; background: transparent;")
            s_lbl.setWordWrap(True)
            text_col.addWidget(s_lbl)
            
        row.addLayout(text_col, stretch=1)
        row.addWidget(control_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return row
        row.addWidget(control_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return row

    def _create_page_header(self, title: str, subtitle: str) -> QWidget:
        header_widget = QWidget()
        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(3)
        
        t = QLabel(title)
        t.setStyleSheet("font-size: 20px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(t)
        
        s = QLabel(subtitle)
        s.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        s.setWordWrap(True)
        layout.addWidget(s)
        return header_widget

    # =========================================================================
    # PAGE 1: DỊCH THUẬT (TRANSLATION)
    # =========================================================================
    def _build_trans_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        layout.addWidget(self._create_page_header(
            "Dịch Thuật",
            "Điều khiển tiến trình dịch và thiết lập phương thức bắt câu thoại thời gian thực"
        ))
        
        # 1. Action Control Card
        ctrl_card, ctrl_layout = self._create_card(
            "Điều Khiển Chính",
            "Bật/Tắt tiến trình dịch và quản lý các cửa sổ phụ trợ"
        )
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)
        
        self.btn_start_stop = QPushButton("▶ Bắt Đầu Dịch")
        self.btn_start_stop.setObjectName("primary-btn")
        self.btn_start_stop.setFixedHeight(38)
        self.btn_start_stop.setMinimumWidth(140)
        self.btn_start_stop.clicked.connect(self._toggle_running)
        btn_bar.addWidget(self.btn_start_stop, stretch=3)
        
        self.btn_overlay = QPushButton("📺 Khung Phụ Đề")
        self.btn_overlay.setFixedHeight(38)
        self.btn_overlay.setMinimumWidth(110)
        self.btn_overlay.clicked.connect(self.toggle_overlay_requested.emit)
        btn_bar.addWidget(self.btn_overlay, stretch=2)
        
        self.btn_backlog = QPushButton("📜 Lịch Sử Thoại")
        self.btn_backlog.setFixedHeight(38)
        self.btn_backlog.setMinimumWidth(110)
        self.btn_backlog.clicked.connect(self.toggle_backlog_requested.emit)
        btn_bar.addWidget(self.btn_backlog, stretch=2)
        
        ctrl_layout.addLayout(btn_bar)
        layout.addWidget(ctrl_card)

        # 2. Provider & Language Settings Card
        cfg_card, cfg_layout = self._create_card(
            "Cấu Hình AI & Ngôn Ngữ",
            "Lựa chọn mô hình ngôn ngữ và cặp ngôn ngữ dịch thuật"
        )
        
        # AI Provider
        self.cb_provider = QComboBox()
        self.cb_provider.setMinimumWidth(230)
        self.cb_provider.setMaximumWidth(280)
        self.cb_provider.addItems([
            "Google Gemini (gemini-2.5-flash) [Khuyên dùng]",
            "OpenAI (gpt-4o-mini)",
            "DeepSeek (deepseek-chat V3/R1)",
            "Anthropic Claude (claude-3-5-haiku)",
            "Groq (llama-3.3-70b) [Siêu tốc]",
            "OpenRouter (Đa mô hình)",
            "Custom Endpoint / Local LLM"
        ])
        self.cb_provider.currentIndexChanged.connect(self._on_provider_changed)
        cfg_layout.addLayout(self._create_setting_row(
            "Nhà cung cấp AI",
            "Dịch vụ AI đảm nhận việc dịch câu thoại",
            self.cb_provider
        ))
        
        # Language Pair
        lang_row_widget = QWidget()
        lang_h = QHBoxLayout(lang_row_widget)
        lang_h.setContentsMargins(0, 0, 0, 0)
        lang_h.setSpacing(6)
        
        self.cb_src_lang = QComboBox()
        self.cb_src_lang.setFixedWidth(130)
        self.cb_src_lang.addItems(["Tiếng Nhật (ja)", "Tiếng Anh (en)", "Tiếng Trung (zh)", "Tiếng Hàn (ko)"])
        self.cb_src_lang.currentIndexChanged.connect(self._on_language_changed)
        lang_h.addWidget(self.cb_src_lang)
        
        arrow = QLabel("➔")
        arrow.setStyleSheet("font-size: 13px; font-weight: bold; color: #60CDFF;")
        lang_h.addWidget(arrow)
        
        self.cb_tgt_lang = QComboBox()
        self.cb_tgt_lang.setFixedWidth(120)
        self.cb_tgt_lang.addItems(["Tiếng Việt (vi)", "Tiếng Anh (en)"])
        self.cb_tgt_lang.currentIndexChanged.connect(self._on_language_changed)
        lang_h.addWidget(self.cb_tgt_lang)
        
        cfg_layout.addLayout(self._create_setting_row(
            "Cặp ngôn ngữ",
            "Ngôn ngữ game gốc và ngôn ngữ hiển thị",
            lang_row_widget
        ))
        
        # Clean WinUI 3 setting rows for options
        self.chk_hybrid = QCheckBox("Bật")
        self.chk_hybrid.setChecked(True)
        self.chk_hybrid.stateChanged.connect(self._save_trans_settings)
        cfg_layout.addLayout(self._create_setting_row(
            "Chế độ Lai Hybrid (Khuyên dùng)",
            "Dịch thô bằng mô hình cục bộ và nhờ AI trau chuốt giúp tiết kiệm token",
            self.chk_hybrid
        ))
        
        self.chk_offline = QCheckBox("Bật")
        self.chk_offline.stateChanged.connect(self._save_trans_settings)
        cfg_layout.addLayout(self._create_setting_row(
            "Chế độ Offline 100%",
            "Chỉ dùng mô hình dịch cục bộ trên máy, hoàn toàn miễn phí và không cần mạng",
            self.chk_offline
        ))
        
        layout.addWidget(cfg_card)

        # 3. Capture Mechanism Card
        cap_card, cap_layout = self._create_card(
            "Cơ Chế Bắt Chữ",
            "Cách thức lấy văn bản từ cửa sổ game Visual Novel"
        )
        
        self.chk_clipboard = QCheckBox("Bật")
        self.chk_clipboard.setChecked(True)
        self.chk_clipboard.stateChanged.connect(self._save_trans_settings)
        cap_layout.addLayout(self._create_setting_row(
            "Bắt chữ Clipboard / Game Hook (Chính)",
            "Tự động nhận diện khi Textractor gửi text vào Clipboard",
            self.chk_clipboard
        ))
        
        ocr_ctrl_widget = QWidget()
        ocr_ctrl_h = QHBoxLayout(ocr_ctrl_widget)
        ocr_ctrl_h.setContentsMargins(0, 0, 0, 0)
        ocr_ctrl_h.setSpacing(8)
        
        self.chk_ocr = QCheckBox("Bật")
        self.chk_ocr.stateChanged.connect(self._save_trans_settings)
        ocr_ctrl_h.addWidget(self.chk_ocr)
        
        btn_ocr = QPushButton("📐 Chọn Vùng (Ctrl+F3)")
        btn_ocr.clicked.connect(self.select_ocr_region_requested.emit)
        ocr_ctrl_h.addWidget(btn_ocr)
        
        cap_layout.addLayout(self._create_setting_row(
            "Quét màn hình OCR (Phụ trợ)",
            "Chụp và nhận diện chữ trên khung thoại game bằng OCR",
            ocr_ctrl_widget
        ))
        layout.addWidget(cap_card)

        # 4. Latest Dialogue Preview Card
        log_card, log_layout = self._create_card("Câu Thoại Vừa Dịch Gần Nhất", "")
        self.lbl_latest_src = QLabel("Chưa có dữ liệu...")
        self.lbl_latest_src.setStyleSheet("color: #8E9BB0; font-size: 12px;")
        self.lbl_latest_src.setWordWrap(True)
        self.lbl_latest_tgt = QLabel("Khung phụ đề đang chờ câu thoại tiếp theo...")
        self.lbl_latest_tgt.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600;")
        self.lbl_latest_tgt.setWordWrap(True)
        log_layout.addWidget(self.lbl_latest_src)
        log_layout.addWidget(self.lbl_latest_tgt)
        layout.addWidget(log_card)
        
        layout.addStretch()
        self.pages_stack.addWidget(page)

    # =========================================================================
    # PAGE 2: TEXTRACTOR HOOK
    # =========================================================================
    def _build_textractor_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        layout.addWidget(self._create_page_header(
            "Textractor Hook",
            "Kết nối trực tiếp vào RAM tiến trình game để bắt chữ chính xác 100%"
        ))
        
        # 1. Status & Quick Launch Card
        status_card, sc_layout = self._create_card(
            "Khởi Chạy Textractor Tích Hợp",
            "Phiên bản Textractor v5.2.0 Portable đi kèm sẵn sàng sử dụng"
        )
        
        btn_h = QHBoxLayout()
        btn_h.setSpacing(10)
        
        btn_x86 = QPushButton("🚀 Mở Textractor (32-bit x86)")
        btn_x86.setObjectName("primary-btn")
        btn_x86.setFixedHeight(38)
        btn_x86.setMinimumWidth(180)
        btn_x86.clicked.connect(lambda: self._launch_textractor("x86"))
        btn_h.addWidget(btn_x86)
        
        btn_x64 = QPushButton("🚀 Mở Textractor (64-bit x64)")
        btn_x64.setFixedHeight(38)
        btn_x64.setMinimumWidth(180)
        btn_x64.clicked.connect(lambda: self._launch_textractor("x64"))
        btn_h.addWidget(btn_x64)
        sc_layout.addLayout(btn_h)
        layout.addWidget(status_card)

        # 2. Guide Card
        guide_card, gc_layout = self._create_card("Hướng Dẫn Nhanh 3 Bước", "")
        guide_text = (
            "<b>Bước 1:</b> Mở Game Visual Novel của bạn lên, sau đó bấm nút <b>Mở Textractor (32-bit)</b> ở trên.<br>"
            "<b>Bước 2:</b> Trong Textractor, bấm nút <b>Attach to game</b> ➔ Chọn file <code>.exe</code> của game.<br>"
            "<b>Bước 3:</b> Quay lại AetherVN bấm <b>▶ Bắt Đầu Dịch</b>. Phụ đề tiếng Việt sẽ tự động nổi lên trên game!"
        )
        guide_lbl = QLabel(guide_text)
        guide_lbl.setStyleSheet("color: #D6D6D6; font-size: 13px; line-height: 1.6;")
        guide_lbl.setWordWrap(True)
        gc_layout.addWidget(guide_lbl)
        layout.addWidget(guide_card)

        # 3. Running Processes Card
        proc_card, pc_layout = self._create_card(
            "Tiến Trình Game Đang Chạy",
            "Danh sách các ứng dụng có thể chọn Attach trong Textractor"
        )
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Tiến trình phát hiện trên hệ thống:"))
        top_row.addStretch()
        
        btn_ref = QPushButton("🔄 Làm Mới")
        btn_ref.clicked.connect(self._refresh_running_processes)
        top_row.addWidget(btn_ref)
        pc_layout.addLayout(top_row)
        
        self.table_procs = QTableWidget()
        self.table_procs.setColumnCount(2)
        self.table_procs.setHorizontalHeaderLabels(["Tên Tiến Trình (Game .exe)", "Mã PID"])
        self.table_procs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_procs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_procs.setColumnWidth(1, 90)
        self.table_procs.setMinimumHeight(200)
        pc_layout.addWidget(self.table_procs)
        
        layout.addWidget(proc_card)
        self._refresh_running_processes()
        
        layout.addStretch()
        self.pages_stack.addWidget(page)

    def _launch_textractor(self, arch: str):
        success = self.textractor_manager.launch_gui(arch)
        if success:
            QMessageBox.information(
                self, "Thông Báo",
                f"Đã khởi chạy Textractor ({arch}) thành công!\n\n"
                "Bây giờ bạn chỉ cần chọn 'Attach to game' trong Textractor và bấm 'Bắt Đầu Dịch' trên AetherVN."
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

    # =========================================================================
    # PAGE 3: NHÀ CUNG CẤP AI (API KEYS)
    # =========================================================================
    def _build_keys_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        layout.addWidget(self._create_page_header(
            "Nhà Cung Cấp AI",
            "Quản lý API Key các mô hình ngôn ngữ lớn (Google Gemini, OpenAI, DeepSeek...)"
        ))
        
        # 1. Gemini Help Card
        help_card, hc_layout = self._create_card(
            "Google Gemini API Key (Miễn Phí)",
            "Gemini Flash có tốc độ phản hồi cực nhanh dưới 300ms và văn phong tự nhiên"
        )
        h_row = QHBoxLayout()
        h_desc = QLabel("💡 Lấy API Key miễn phí tại Google AI Studio:")
        h_desc.setStyleSheet("color: #C0C0C0; font-size: 12px;")
        h_row.addWidget(h_desc)
        h_row.addStretch()
        
        btn_ai_studio = QPushButton("🔗 Mở Google AI Studio")
        btn_ai_studio.setObjectName("primary-btn")
        btn_ai_studio.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        h_row.addWidget(btn_ai_studio)
        hc_layout.addLayout(h_row)
        layout.addWidget(help_card)

        # 2. Key Inputs Card
        keys_card, kc_layout = self._create_card(
            "Danh Sách API Keys",
            "Nhập khóa API cho các nhà cung cấp bạn muốn sử dụng"
        )
        
        providers = [
            ("gemini", "Google Gemini API Key", "Mô hình: gemini-2.5-flash / 2.0-flash"),
            ("openai", "OpenAI API Key", "Mô hình: gpt-4o-mini / gpt-4o"),
            ("deepseek", "DeepSeek API Key", "Mô hình: deepseek-chat (V3/R1)"),
            ("claude", "Anthropic Claude API Key", "Mô hình: claude-3-5-haiku / sonnet"),
            ("groq", "Groq API Key", "Mô hình: llama-3.3-70b (Siêu tốc)"),
            ("openrouter", "OpenRouter API Key", "Hỗ trợ đa dạng hàng trăm mô hình"),
            ("custom", "Custom / Local Endpoint Key", "Dùng cho Ollama, LM Studio, vLLM")
        ]
        
        for p_id, p_title, p_desc in providers:
            row_widget = QWidget()
            row_h = QHBoxLayout(row_widget)
            row_h.setContentsMargins(0, 0, 0, 0)
            row_h.setSpacing(6)
            
            le = QLineEdit()
            le.setEchoMode(QLineEdit.EchoMode.Password)
            le.setPlaceholderText(f"Nhập API key cho {p_id}...")
            le.setFixedWidth(190)
            le.textChanged.connect(self._save_keys)
            self.key_inputs[p_id] = le
            row_h.addWidget(le)
            
            toggle_eye = QPushButton("👁")
            toggle_eye.setFixedWidth(32)
            toggle_eye.setToolTip("Ẩn/Hiện ký tự")
            toggle_eye.clicked.connect(lambda ch=False, target=le: self._toggle_echo_mode(target))
            row_h.addWidget(toggle_eye)
            
            test_btn = QPushButton("Test")
            test_btn.setFixedWidth(50)
            test_btn.setToolTip("Kiểm tra kết nối tới API này")
            test_btn.clicked.connect(lambda ch=False, pid=p_id: self.test_api_requested.emit(pid))
            row_h.addWidget(test_btn)
            
            kc_layout.addLayout(self._create_setting_row(p_title, p_desc, row_widget))

        # Custom Endpoint URL
        self.le_custom_url = QLineEdit()
        self.le_custom_url.setPlaceholderText("http://localhost:11434/v1")
        self.le_custom_url.setFixedWidth(284)
        self.le_custom_url.textChanged.connect(self._save_keys)
        kc_layout.addLayout(self._create_setting_row(
            "Custom Base URL",
            "Đường dẫn máy chủ LLM chạy cục bộ (Ollama, LM Studio...)",
            self.le_custom_url
        ))
        layout.addWidget(keys_card)

        # 3. System Prompt Customization Card
        sp_card, sp_layout = self._create_card(
            "System Prompt Tùy Chỉnh",
            "Hướng dẫn văn phong dịch thuật gửi kèm cho AI (để trống sẽ dùng prompt chuẩn chuyên gia)"
        )
        
        sp_top = QHBoxLayout()
        sp_top.addStretch()
        btn_reset_p = QPushButton("🔄 Khôi phục Prompt chuẩn")
        btn_reset_p.clicked.connect(self._reset_system_prompt_to_default)
        sp_top.addWidget(btn_reset_p)
        sp_layout.addLayout(sp_top)
        
        self.te_system_prompt = QTextEdit()
        self.te_system_prompt.setMaximumHeight(85)
        self.te_system_prompt.textChanged.connect(self._save_keys)
        sp_layout.addWidget(self.te_system_prompt)
        layout.addWidget(sp_card)
        
        layout.addStretch()
        self.pages_stack.addWidget(page)

    def _toggle_echo_mode(self, line_edit: QLineEdit):
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)

    # =========================================================================
    # PAGE 4: TỪ ĐIỂN & XƯNG HÔ (GLOSSARY)
    # =========================================================================
    def _build_glossary_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        layout.addWidget(self._create_page_header(
            "Từ Điển & Danh Xưng",
            "Thiết lập cách dịch tên nhân vật, danh xưng và thuật ngữ riêng trong Visual Novel"
        ))
        
        # 1. Add Rule Card
        add_card, ac_layout = self._create_card(
            "Thêm Quy Tắc Mới",
            "Định nghĩa cách dịch cố định cho các từ khóa hoặc nhân xưng"
        )
        add_row = QHBoxLayout()
        add_row.setSpacing(10)
        
        self.le_orig = QLineEdit()
        self.le_orig.setPlaceholderText("Từ gốc (VD: 先輩, 桜, 俺)")
        add_row.addWidget(self.le_orig, stretch=2)
        
        self.le_trans = QLineEdit()
        self.le_trans.setPlaceholderText("Bản dịch mong muốn (VD: Tiền bối, Sakura, Tôi)")
        add_row.addWidget(self.le_trans, stretch=2)
        
        btn_add = QPushButton("➕ Thêm Quy Tắc")
        btn_add.setObjectName("primary-btn")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._add_glossary_item)
        add_row.addWidget(btn_add, stretch=1)
        ac_layout.addLayout(add_row)
        layout.addWidget(add_card)

        # 2. Table Card
        tbl_card, tc_layout = self._create_card(
            "Danh Sách Quy Tắc Đang Áp Dụng",
            "Toàn bộ quy tắc dưới đây sẽ được tự động tích hợp vào câu lệnh AI"
        )
        self.table_glossary = QTableWidget()
        self.table_glossary.setColumnCount(3)
        self.table_glossary.setHorizontalHeaderLabels(["Từ Gốc", "Bản Dịch / Xưng Hô", "Thao Tác"])
        self.table_glossary.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_glossary.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_glossary.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_glossary.setColumnWidth(2, 80)
        self.table_glossary.setMinimumHeight(240)
        tc_layout.addWidget(self.table_glossary)
        layout.addWidget(tbl_card)
        
        layout.addStretch()
        self.pages_stack.addWidget(page)

    # =========================================================================
    # PAGE 5: GIAO DIỆN PHỤ ĐỀ (APPEARANCE)
    # =========================================================================
    def _build_appearance_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        layout.addWidget(self._create_page_header(
            "Giao Diện Phụ Đề",
            "Tùy biến kích thước, font chữ, màu sắc và viền của khung phụ đề nổi trên màn hình"
        ))
        
        # 1. Typography & Colors Card
        style_card, sc_layout = self._create_card(
            "Kiểu Chữ & Màu Sắc",
            "Định dạng chữ giúp câu thoại luôn sắc nét và dễ đọc trên nền game"
        )
        
        self.cb_font = QComboBox()
        self.cb_font.setMinimumWidth(200)
        self.cb_font.setMaximumWidth(260)
        self.cb_font.setMaxVisibleItems(16)
        self._populate_font_list()
        self.cb_font.currentIndexChanged.connect(self._save_appearance)
        self.fc_font = self.cb_font  # alias for backwards compatibility
        sc_layout.addLayout(self._create_setting_row("Font chữ", "Phông chữ hiển thị phụ đề", self.cb_font))
        
        self.sp_font_size = QSpinBox()
        self.sp_font_size.setRange(12, 48)
        self.sp_font_size.setValue(18)
        self.sp_font_size.setFixedWidth(80)
        self.sp_font_size.valueChanged.connect(self._save_appearance)
        sc_layout.addLayout(self._create_setting_row("Cỡ chữ (px)", "Kích cỡ chữ câu thoại đã dịch", self.sp_font_size))
        
        col_box = QWidget()
        col_h = QHBoxLayout(col_box)
        col_h.setContentsMargins(0, 0, 0, 0)
        col_h.setSpacing(6)
        
        self.btn_text_color = QPushButton("Màu Chữ")
        self.btn_text_color.setFixedWidth(85)
        self.btn_text_color.clicked.connect(self._pick_text_color)
        col_h.addWidget(self.btn_text_color)
        
        self.btn_outline_color = QPushButton("Màu Viền")
        self.btn_outline_color.setFixedWidth(85)
        self.btn_outline_color.clicked.connect(self._pick_outline_color)
        col_h.addWidget(self.btn_outline_color)
        sc_layout.addLayout(self._create_setting_row("Bảng màu", "Màu sắc chữ và đường viền chống chói", col_box))
        
        self.sp_outline_width = QSpinBox()
        self.sp_outline_width.setRange(0, 6)
        self.sp_outline_width.setValue(2)
        self.sp_outline_width.setFixedWidth(80)
        self.sp_outline_width.valueChanged.connect(self._save_appearance)
        sc_layout.addLayout(self._create_setting_row("Độ dày viền (px)", "Độ dày viền chống bóng mờ", self.sp_outline_width))
        
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sl_opacity.setRange(0, 100)
        self.sl_opacity.setValue(85)
        self.sl_opacity.setFixedWidth(140)
        self.sl_opacity.valueChanged.connect(self._save_appearance)
        sc_layout.addLayout(self._create_setting_row("Độ mờ đục nền (%)", "Độ trong suốt của khung phụ đề", self.sl_opacity))
        
        self.chk_show_source = QCheckBox("Bật")
        self.chk_show_source.setChecked(True)
        self.chk_show_source.stateChanged.connect(self._save_appearance)
        sc_layout.addLayout(self._create_setting_row("Hiển thị câu thoại gốc", "Hiện câu tiếng Nhật/Anh gốc phía trên bản dịch", self.chk_show_source))
        
        layout.addWidget(style_card)

        # 2. Dimensions & Presets Card
        dim_card, dc_layout = self._create_card(
            "Kích Thước Khung Phụ Đề",
            "Kích thước khung hiển thị (bạn cũng có thể kéo chuột trực tiếp tại góc khung)"
        )
        
        dim_box = QWidget()
        dim_h = QHBoxLayout(dim_box)
        dim_h.setContentsMargins(0, 0, 0, 0)
        dim_h.setSpacing(6)
        
        dim_h.addWidget(QLabel("Rộng:"))
        self.sp_overlay_width = QSpinBox()
        self.sp_overlay_width.setRange(350, 3840)
        self.sp_overlay_width.setSingleStep(50)
        self.sp_overlay_width.setValue(1150)
        self.sp_overlay_width.setFixedWidth(95)
        self.sp_overlay_width.valueChanged.connect(self._save_appearance)
        dim_h.addWidget(self.sp_overlay_width)
        
        dim_h.addWidget(QLabel("Cao:"))
        self.sp_overlay_height = QSpinBox()
        self.sp_overlay_height.setRange(90, 2160)
        self.sp_overlay_height.setSingleStep(20)
        self.sp_overlay_height.setValue(230)
        self.sp_overlay_height.setFixedWidth(85)
        self.sp_overlay_height.valueChanged.connect(self._save_appearance)
        dim_h.addWidget(self.sp_overlay_height)
        dc_layout.addLayout(self._create_setting_row("Độ phân giải khung", "Chiều rộng và chiều cao tính bằng pixel", dim_box))
        
        preset_row = QHBoxLayout()
        preset_row.setSpacing(10)
        
        btn_compact = QPushButton("📐 Gọn (900x160)")
        btn_compact.clicked.connect(lambda: self._set_overlay_size(900, 160))
        preset_row.addWidget(btn_compact)
        
        btn_std = QPushButton("🖥 Chuẩn (1150x230)")
        btn_std.setObjectName("primary-btn")
        btn_std.clicked.connect(lambda: self._set_overlay_size(1150, 230))
        preset_row.addWidget(btn_std)
        
        btn_wide = QPushButton("🎬 Siêu Rộng (1450x280)")
        btn_wide.clicked.connect(lambda: self._set_overlay_size(1450, 280))
        preset_row.addWidget(btn_wide)
        dc_layout.addLayout(preset_row)
        
        layout.addWidget(dim_card)
        layout.addStretch()
        self.pages_stack.addWidget(page)

    # =========================================================================
    # PAGE 6: GIỌNG ĐỌC & PHÍM TẮT (TTS & HOTKEYS)
    # =========================================================================
    def _build_tts_hotkeys_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        layout.addWidget(self._create_page_header(
            "Giọng Đọc & Phím Tắt",
            "Cấu hình Microsoft Edge-TTS và các phím tắt toàn cục"
        ))
        
        # 1. TTS Card
        tts_card, tc_layout = self._create_card(
            "Giọng Đọc AI (Edge-TTS)",
            "Tự động chuyển câu thoại tiếng Việt thành giọng đọc tự nhiên miễn phí"
        )
        
        self.chk_auto_tts = QCheckBox("Bật")
        self.chk_auto_tts.stateChanged.connect(self._save_tts)
        tc_layout.addLayout(self._create_setting_row(
            "Tự động phát giọng đọc",
            "Tự phát âm thanh ngay sau khi câu thoại vừa được dịch xong",
            self.chk_auto_tts
        ))
        
        self.cb_tts_voice = QComboBox()
        self.cb_tts_voice.setMinimumWidth(220)
        self.cb_tts_voice.setMaximumWidth(280)
        from src.core.tts_player import TTSPlayer
        for k, v in TTSPlayer.VOICE_LIST.items():
            self.cb_tts_voice.addItem(v, k)
        self.cb_tts_voice.currentIndexChanged.connect(self._save_tts)
        tc_layout.addLayout(self._create_setting_row(
            "Giọng đọc",
            "Chọn giọng đọc tiếng Việt hoặc tiếng Nhật ưa thích",
            self.cb_tts_voice
        ))
        layout.addWidget(tts_card)

        # 2. Hotkeys Card
        hk_card, hk_layout = self._create_card(
            "Phím Tắt Toàn Cục (Global Hotkeys)",
            "Thao tác nhanh ngay khi đang ở trong cửa sổ game Visual Novel"
        )
        
        hotkeys_info = [
            ("Ctrl + F1", "Khóa / Mở Click-Through (cho phép chuột click xuyên qua phụ đề vào game)"),
            ("Ctrl + F2", "Tạm dừng / Tiếp tục tiến trình dịch"),
            ("Ctrl + F3", "Kéo chuột chọn lại vùng quét màn hình OCR"),
            ("Ctrl + F4", "Ẩn / Hiện nhanh khung phụ đề nổi"),
            ("Ctrl + F5", "Đọc lại câu thoại vừa dịch bằng giọng TTS")
        ]
        
        for key, desc in hotkeys_info:
            row = QHBoxLayout()
            row.setContentsMargins(0, 3, 0, 3)
            row.setSpacing(12)
            
            badge = QLabel(key)
            badge.setStyleSheet("background: #1F1F1F; color: #60CDFF; font-weight: 600; padding: 4px 8px; border-radius: 4px; border: 1px solid #363636; font-family: monospace;")
            badge.setFixedWidth(85)
            row.addWidget(badge)
            
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet("color: #D2D2D2; font-size: 13px;")
            d_lbl.setWordWrap(True)
            row.addWidget(d_lbl, stretch=1)
            hk_layout.addLayout(row)
            
        layout.addWidget(hk_card)
        layout.addStretch()
        self.pages_stack.addWidget(page)

    # =========================================================================
    # EVENT HANDLERS & LOGIC
    # =========================================================================
    def _toggle_running(self):
        if self.btn_start_stop.text().startswith("▶"):
            self.start_requested.emit()
            self.btn_start_stop.setText("⏸ Tạm Dừng Dịch")
            self.btn_start_stop.setObjectName("danger-btn")
            self.btn_start_stop.setStyle(self.btn_start_stop.style())
            self.status_badge.setText("🟢 ĐANG HOẠT ĐỘNG")
            self.status_badge.setStyleSheet("color: #34D399; font-weight: 600; font-size: 12px;")
        else:
            self.pause_requested.emit()
            self.btn_start_stop.setText("▶ Bắt Đầu Dịch")
            self.btn_start_stop.setObjectName("primary-btn")
            self.btn_start_stop.setStyle(self.btn_start_stop.style())
            self.status_badge.setText("⏸ TẠM DỪNG")
            self.status_badge.setStyleSheet("color: #FBBF24; font-weight: 600; font-size: 12px;")

    def _on_provider_changed(self, idx: int):
        providers = ["gemini", "openai", "deepseek", "claude", "groq", "openrouter", "custom"]
        if idx < len(providers):
            self.settings.set("selected_provider", providers[idx])
            self.settings.save()

    def _on_language_changed(self):
        src_map = {0: "ja", 1: "en", 2: "zh", 3: "ko"}
        tgt_map = {0: "vi", 1: "en"}
        src = src_map.get(self.cb_src_lang.currentIndex(), "ja")
        tgt = tgt_map.get(self.cb_tgt_lang.currentIndex(), "vi")
        self.settings.set("source_language", src)
        self.settings.set("target_language", tgt)
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
            self.appearance_changed.emit()

    def _pick_outline_color(self):
        col = QColorDialog.getColor(initial=QColor(self.settings.get("overlay", {}).get("outline_color", "#05050A")), parent=self)
        if col.isValid():
            overlay_cfg = self.settings.get("overlay", {})
            overlay_cfg["outline_color"] = col.name()
            self.settings.set("overlay", overlay_cfg)
            self.settings.save()
            self.appearance_changed.emit()

    def _save_appearance(self):
        overlay_cfg = self.settings.get("overlay", {})
        if hasattr(self, 'cb_font'):
            font_txt = self.cb_font.currentText().strip()
            if font_txt:
                overlay_cfg["font_family"] = font_txt
        elif hasattr(self, 'fc_font') and hasattr(self.fc_font, 'currentFont'):
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

    def _populate_font_list(self):
        from PySide6.QtGui import QFontDatabase
        self.cb_font.clear()
        
        curated_fonts = [
            "Segoe UI",
            "Be Vietnam Pro",
            "Roboto",
            "Montserrat",
            "Arial",
            "Tahoma",
            "Verdana",
            "Calibri",
            "Noto Sans",
            "Open Sans",
            "Georgia",
            "Times New Roman",
            "Trebuchet MS",
            "Consolas",
            "Comic Sans MS",
            "Impact"
        ]
        
        # Add curated subtitle fonts first
        for font_name in curated_fonts:
            self.cb_font.addItem(font_name)
            
        # Add separator between curated and full system fonts
        self.cb_font.insertSeparator(len(curated_fonts))
        
        # Add all other installed system fonts
        all_sys_fonts = QFontDatabase.families()
        curated_set = set(curated_fonts)
        for font_name in sorted(all_sys_fonts):
            if font_name not in curated_set and not font_name.startswith("@"):
                self.cb_font.addItem(font_name)
                
        # Preview each font in its own style inside the dropdown list
        for i in range(self.cb_font.count()):
            name = self.cb_font.itemText(i)
            if name:
                self.cb_font.setItemData(i, QFont(name, 11), Qt.ItemDataRole.FontRole)

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
            del_btn.setStyleSheet("background: rgba(239, 68, 68, 0.2); color: #F87171; border: none; border-radius: 4px; padding: 4px;")
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
            
        # Language Pair
        src = self.settings.get("source_language", "ja")
        tgt = self.settings.get("target_language", "vi")
        src_rev = {"ja": 0, "en": 1, "zh": 2, "ko": 3}
        tgt_rev = {"vi": 0, "en": 1}
        self.cb_src_lang.blockSignals(True)
        self.cb_tgt_lang.blockSignals(True)
        self.cb_src_lang.setCurrentIndex(src_rev.get(src, 0))
        self.cb_tgt_lang.setCurrentIndex(tgt_rev.get(tgt, 0))
        self.cb_src_lang.blockSignals(False)
        self.cb_tgt_lang.blockSignals(False)

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
        font_name = ov.get("font_family", "Segoe UI")
        if hasattr(self, 'cb_font'):
            idx = self.cb_font.findText(font_name)
            if idx >= 0:
                self.cb_font.setCurrentIndex(idx)
            else:
                self.cb_font.insertItem(0, font_name)
                self.cb_font.setCurrentIndex(0)
        elif hasattr(self, 'fc_font') and hasattr(self.fc_font, 'setCurrentFont'):
            self.fc_font.setCurrentFont(QFont(font_name))
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

    def closeEvent(self, event):
        """When main control panel is closed, cleanly shutdown entire application."""
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()
