import os
import json
import copy
from typing import Any, Dict

DEFAULT_SETTINGS: Dict[str, Any] = {
    "selected_provider": "gemini",
    "source_language": "ja",
    "target_language": "vi",
    "system_prompt": (
        "Bạn là chuyên gia dịch thuật và bản địa hóa Visual Novel / Anime / Game hàng đầu sang Tiếng Việt.\n"
        "Nhiệm vụ của bạn: Dịch câu thoại/văn bản gốc sang Tiếng Việt một cách tự nhiên, mượt mà, giàu cảm xúc và chuẩn ngữ cảnh.\n\n"
        "### NGUYÊN TẮC DỊCH THUẬT QUAN TRỌNG:\n"
        "1. VĂN PHONG TỰ NHIÊN: Dịch thoát ý và trau chuốt, tuyệt đối KHÔNG dịch thô hay dịch từng từ kiểu máy móc (Word-by-word/Google Translate).\n"
        "2. XƯNG HÔ & ĐẠI TỪ: Tuân thủ nghiêm ngặt bảng từ điển (Glossary) và ngữ cảnh mối quan hệ giữa các nhân vật (Tôi - Cậu, Anh - Em, Tiền bối - Hậu bối, v.v.).\n"
        "3. DẤU CÂU & CẢM XÚC: Giữ nguyên các dấu ngắt nghỉ cảm xúc đặc trưng của Visual Novel: ba chấm '...', chấm than '!', chấm hỏi '?', dấu gạch ngang '――', v.v.\n"
        "4. ĐỊNH DẠNG TÊN NHÂN VẬT: Nếu câu bắt đầu bằng tên trong ngoặc vuông như 【Tên】, hãy giữ nguyên dạng 【Tên】 hoặc dịch tên theo glossary.\n"
        "5. ĐẦU RA TUYỆT ĐỐI CHUẨN XÁC:\n"
        "   - Chỉ xuất DUY NHẤT câu văn bản dịch tiếng Việt hoàn chỉnh.\n"
        "   - Tuyệt đối KHÔNG thêm giải thích, KHÔNG ghi tiền tố như 'Bản dịch:', KHÔNG bọc toàn bộ câu trong dấu ngoặc kép hay markdown block."
    ),
    "providers": {
        "gemini": {
            "api_key": "",
            "model": "gemini-3.5-flash-lite",
            "base_url": "https://generativelanguage.googleapis.com"
        },
        "openai": {
            "api_key": "",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1"
        },
        "deepseek": {
            "api_key": "",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1"
        },
        "claude": {
            "api_key": "",
            "model": "claude-3-5-haiku-20241022",
            "base_url": "https://api.anthropic.com/v1"
        },
        "groq": {
            "api_key": "",
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"
        },
        "openrouter": {
            "api_key": "",
            "model": "google/gemini-2.0-flash-001",
            "base_url": "https://openrouter.ai/api/v1"
        },
        "custom": {
            "api_key": "",
            "model": "default",
            "base_url": "http://localhost:11434/v1"
        }
    },
    "hybrid_mode": True,
    "offline_only": False,
    "clipboard": {
        "enabled": True,
        "debounce_ms": 250
    },
    "ocr": {
        "enabled": False,
        "region": [100, 700, 1080, 200],  # x, y, width, height
        "scan_interval_ms": 150,
        "engine": "rapidocr"
    },
    "overlay": {
        "geometry": [250, 720, 850, 130],
        "font_family": "Segoe UI",
        "font_size": 18,
        "font_weight": "bold",
        "text_color": "#FFFFFF",
        "outline_color": "#05050A",
        "outline_width": 2,
        "bg_color": "rgba(18, 20, 29, 0.85)",
        "bg_opacity": 85,
        "click_through": False,
        "show_source_text": True,
        "source_font_size": 13,
        "source_text_color": "#A0A8C0"
    },
    "tts": {
        "enabled": False,
        "voice": "vi-VN-HoaiMyNeural",
        "rate": "+0%",
        "volume": "+0%"
    },
    "hotkeys": {
        "toggle_click_through": "<ctrl>+<f1>",
        "pause_resume": "<ctrl>+<f2>",
        "select_ocr_region": "<ctrl>+<f3>",
        "toggle_overlay_visibility": "<ctrl>+<f4>",
        "replay_tts": "<ctrl>+<f5>"
    },
    "glossary": {}
}

class AppSettings:
    """Manages application persistent configuration."""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = config_path
        self._settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Load settings from JSON file, creating default if not exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._deep_update(self._settings, loaded)
            except Exception as e:
                print(f"[Settings] Error loading config: {e}. Using defaults.")
        else:
            self.save()

    def save(self) -> None:
        """Save settings to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Settings] Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        return self._settings.get("providers", {}).get(provider, {})

    def get_provider_key(self, provider: str) -> str:
        return self.get_provider_config(provider).get("api_key", "")

    def set_provider_key(self, provider: str, key: str) -> None:
        if "providers" not in self._settings:
            self._settings["providers"] = {}
        if provider not in self._settings["providers"]:
            self._settings["providers"][provider] = {}
        self._settings["providers"][provider]["api_key"] = key

    def set_glossary_entry(self, original: str, translated: str) -> None:
        if "glossary" not in self._settings:
            self._settings["glossary"] = {}
        self._settings["glossary"][original] = translated

    def remove_glossary_entry(self, original: str) -> None:
        if "glossary" in self._settings and original in self._settings["glossary"]:
            del self._settings["glossary"][original]

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self._settings)

    def _deep_update(self, target: dict, source: dict) -> None:
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._deep_update(target[k], v)
            else:
                target[k] = v
