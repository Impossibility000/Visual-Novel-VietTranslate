# Design Specification: VN Realtime AI Translator (AetherVN)

**Date**: 2026-10-05  
**Project**: VN Realtime AI Translator  
**Tech Stack**: Python 3.10+, PySide6 (Qt for Python), Windows API (`ctypes`), `httpx` (Async API client), `edge-tts`, `pygame` (audio playback), `rapidocr_onnxruntime` / `pytesseract` / Windows Media OCR, `pynput` / `keyboard`.

---

## 1. Overview & Goals

VN Realtime AI Translator is a high-performance, lightweight Windows desktop application designed to translate text in Visual Novels, RPGs, and desktop applications in real-time. It features:
- **Dual Text Input**: Primary input via Hooking/Clipboard/Named-pipe monitor, with secondary fallback via rapid Screen Region OCR.
- **Multi-Provider AI Translation**: Support for Google Gemini (1.5 Flash, 2.0 Flash, 2.5 Flash), OpenAI (GPT-4o, GPT-4o-mini), DeepSeek (V3, R1), Claude (Sonnet, Haiku), Groq, OpenRouter, and custom OpenAI-compatible endpoints with streaming output.
- **Visual Novel Context & Glossary Engine**: Context buffer (3-5 prior lines), character name & honorific mapping (Glossary), and specialized VN system prompts to produce natural Vietnamese translations.
- **Text Cleaner & De-duplication**: Cleaning game control codes, ruby/furigana tags, and typewriter effect deduplication.
- **Modern Floating Overlay & Backlog Window**: Glassmorphism UI, click-through mode, customizable text styling/stroke, plus a complete searchable Dialogue History/Backlog window.
- **Edge-TTS Voice Output**: High-quality free speech synthesis for Japanese and Vietnamese.
- **Global Hotkeys**: Custom system-wide shortcuts for OCR capture, pause/resume, toggle click-through, and subtitle hide/show.

---

## 2. System Architecture

```
+-------------------------------------------------------------------------------+
|                                GUI Layer (PySide6)                            |
|  +---------------------+   +-------------------------+   +-----------------+  |
|  | Main Control Window |   | Floating Subtitle Panel |   | History/Backlog |  |
|  | - API Settings      |   | - Click-through mode    |   | - Searchable    |  |
|  | - Glossary Manager  |   | - Realtime Streaming    |   | - Replay Audio  |  |
|  | - Hotkey & OCR cfg  |   | - Customizable Font/Bg  |   | - Export logs   |  |
|  +---------------------+   +-------------------------+   +-----------------+  |
+---------------------------------------^---------------------------------------+
                                        | Signals / Qt Slots
+---------------------------------------v---------------------------------------+
|                               Controller Core                                 |
|  - App State Manager (Active/Paused, Mode, Settings persistence: config.json) |
|  - Event Dispatcher & Deduplication Pipeline                                 |
+---------^-----------------------------^-----------------------------^---------+
          |                             |                             |
+---------+----------+        +---------+----------+        +---------+---------+
| Text Input Engine  |        |  AI Trans Engine   |        |  Audio/TTS & Hot  |
| - Clipboard Listener|       | - Gemini Client    |        | - Edge-TTS Player |
| - Named Pipe/Socket|        | - OpenAI/DeepSeek  |        | - Global Hotkeys  |
| - Screen Region OCR|        | - Claude Client    |        |   (pynput/WinAPI) |
| - Text Cleaner     |        | - Glossary Filter  |        |                   |
| - Debounce Queue   |        | - Context Memory   |        |                   |
+--------------------+        +--------------------+        +-------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 Text Input & Preprocessing
1. **Clipboard Listener (`src/core/clipboard_listener.py`)**:
   - Monitored via Windows `AddClipboardFormatListener` / Qt clipboard polling with minimum overhead.
   - Detects new text pasted by Textractor, VNR, or user.
2. **Screen OCR Capture (`src/core/ocr_engine.py`)**:
   - Region selector widget (Snip overlay) allowing the user to drag and select the dialogue box coordinate `(x, y, w, h)`.
   - Continuous scanning (configurable interval 200-500ms) with frame change detection (SSIM/image hash comparison to prevent redundant OCR when screen is static).
   - Fast OCR engine using RapidOCR / Windows Media OCR (sub-50ms execution).
3. **Text Cleaner & De-duplicator (`src/core/text_cleaner.py`)**:
   - Regex cleaning for VN tags: Ruby/Furigana `\[.*?\]` or `\{.*?\}`, control codes (`\n`, `\k`, `@`, `\\`), garbage unicode glyphs.
   - Typewriter debouncer: If a new incoming string is an extension of the previous string within `T_debounce` (e.g. 250ms), buffer it until sentence completion.
   - Exact hash deduplication: Prevents re-translating identical text within 2 seconds.

### 3.2 AI Translation & Context Management (`src/core/translator.py`)
1. **Multi-Provider AI Clients**:
   - **Google Gemini**: Using official REST streaming endpoints for high speed (<300ms time to first token).
   - **OpenAI Compatible (OpenAI, DeepSeek, Groq, OpenRouter, Ollama)**: Unified `AsyncOpenAI` / HTTP streaming client.
   - **Anthropic Claude**: Using Claude Messages API streaming.
2. **Glossary & Character Mapping (`src/core/glossary.py`)**:
   - User-defined JSON glossary dictionary `{"original": "translated", ...}`.
   - Pre-translation regex replacement or system prompt injection (`"Translate with strict adherence to: {glossary}"`).
3. **Context Memory (`src/core/context_manager.py`)**:
   - Ring buffer of the last $N$ turns (default 4 sentences).
   - Sent in system prompt:
     ```
     [Context / Previous Dialogues]
     - Speaker A: [Original line 1] -> [Translated line 1]
     - Speaker B: [Original line 2] -> [Translated line 2]
     [Current Sentence to Translate]
     - Speaker: {current_sentence}
     ```

### 3.3 UI Layer (PySide6)
1. **Main Control Panel (`src/ui/main_window.py`)**:
   - Tabs:
     - **Translation**: Start/Stop, Source/Target language, Provider selector, Quick stats (Tokens, Speed).
     - **API Keys**: Masked key inputs for Gemini, OpenAI, DeepSeek, Claude, Groq, OpenRouter, Custom Base URL.
     - **Glossary**: Table editor to add/edit/delete character names and custom terminology.
     - **Appearance**: Subtitle font, size, text color, outline color/thickness, background opacity, blur effect.
     - **Hotkeys**: Configurable keybindings.
2. **Floating Subtitle Overlay (`src/ui/overlay_window.py`)**:
   - Frameless, Always-On-Top window with `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint`.
   - Native Windows API integration for `WS_EX_TRANSPARENT | WS_EX_LAYERED` to enable true click-through.
   - Styled text rendering with QPainterPath or RichText stylesheet for crisp text outlines preventing illegibility against busy game art.
   - Smooth text streaming animation.
3. **Dialogue History / Backlog (`src/ui/backlog_window.py`)**:
   - Scrollable list with timestamp, source text, target text, and a "Replay TTS" button.
   - Search filter bar and export button (JSON / TXT).

### 3.4 Speech Synthesis (Edge-TTS) (`src/core/tts_player.py`)
- Background async worker using `edge-tts`.
- Voices supported:
  - Japanese: `ja-JP-NanamiNeural` (Female), `ja-JP-KeitaNeural` (Male).
  - Vietnamese: `vi-VN-HoaiMyNeural` (Female), `vi-VN-NamMinhNeural` (Male).
  - English: `en-US-JennyNeural`, `en-US-GuyNeural`.
- Audio streaming playback directly via `pygame.mixer` or memory buffer without disk bloat.

### 3.5 Global Hotkeys (`src/core/hotkey_manager.py`)
- Built on `pynput` / Windows `RegisterHotKey`.
- Default Shortcuts:
  - `Ctrl + F1`: Toggle Subtitle Click-Through
  - `Ctrl + F2`: Pause / Resume Translation
  - `Ctrl + F3`: Select New OCR Screen Region
  - `Ctrl + F4`: Quick Show / Hide Overlay
  - `Ctrl + F5`: Replay TTS for Current Sentence

---

## 4. Configuration Storage (`config/settings.json`)
All settings, API keys (optionally encrypted/masked), hotkeys, glossary items, and overlay positions are persisted in `config/settings.json`.

---

## 5. Testing & Verification Plan
1. **Unit Tests**:
   - Text cleaner & ruby filter regex tests (`test_text_cleaner.py`).
   - Glossary injection and replacement tests (`test_glossary.py`).
   - Context buffer rotation tests (`test_context_manager.py`).
2. **Integration Tests**:
   - Mock API translation provider tests (simulated streaming output).
   - OCR mock engine tests.
   - Config load/save persistence validation.
3. **Manual / GUI Verification**:
   - Launch application, verify settings window, floating overlay, and backlog.
   - Test click-through toggling, streaming subtitles, and audio TTS.
