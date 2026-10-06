# VN Realtime AI Translator (AetherVN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a high-performance Windows desktop real-time Visual Novel AI translation application with Clipboard/Text Hooking, Screen Region OCR fallback, Multi-Provider AI (Gemini, OpenAI, DeepSeek, Claude, Groq, OpenRouter), Glossary/Context Memory, Glassmorphism Floating Overlay with Click-through, Backlog history, and Edge-TTS voice.

**Architecture:** PySide6 desktop application with an asynchronous multi-threaded controller. Input pipelines (Clipboard Listener, Screen OCR) feed into a Text Cleaner and Deduplication buffer, pass through a Glossary & Context Manager, stream through the selected AI Translation Provider (REST/SSE streaming), and render onto a transparent Floating Overlay and Backlog window with optional Edge-TTS voice playback.

**Tech Stack:** Python 3.10+, PySide6, `httpx`, `asyncio`, `edge-tts`, `pygame`, `pillow`, `rapidocr_onnxruntime` / `pytesseract` / Windows OCR, `pynput`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-10-05-vn-realtime-ai-translator-design.md`

## Global Constraints
- Target Platform: Windows 10/11 (support standard Windows DPI scaling and `ctypes` for click-through `WS_EX_TRANSPARENT | WS_EX_LAYERED`).
- Async/Non-blocking: No UI freezing during network calls, OCR processing, or TTS playback.
- Config schema: Persisted in `config/settings.json` with sensible defaults.
- All code modules must include comprehensive automated unit and integration tests with `pytest`.

---

### Task 1: Project Setup, Config Management & Settings Schema

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/config/__init__.py`
- Create: `src/config/settings.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Produces: `AppSettings` class with methods `load()`, `save()`, `to_dict()`, `get(key, default)`, `set(key, value)`.

- [ ] **Step 1: Write requirements.txt**
Define dependencies: `PySide6`, `httpx`, `edge-tts`, `pygame`, `pillow`, `rapidocr_onnxruntime`, `pynput`, `pytest`, `pytest-asyncio`.

- [ ] **Step 2: Write failing test for AppSettings**
Test loading default settings, modifying values, persisting to JSON, and reloading.

- [ ] **Step 3: Run test to verify it fails**
Run: `pytest tests/test_settings.py -v`

- [ ] **Step 4: Implement AppSettings**
Support default API keys dict, selected provider, language pair, overlay geometry, font styling, hotkey mapping, and auto-creation of `config/` directory.

- [ ] **Step 5: Run test to verify it passes**
Run: `pytest tests/test_settings.py -v`

---

### Task 2: Text Cleaner, Ruby Filter & Typewriter Deduplicator

**Files:**
- Create: `src/core/__init__.py`
- Create: `src/core/text_cleaner.py`
- Test: `tests/test_text_cleaner.py`

**Interfaces:**
- Produces: `TextCleaner` class with `clean_text(raw_text: str) -> str`, `is_duplicate(cleaned_text: str, ttl_seconds: float = 2.0) -> bool`, and `process_typewriter_chunk(new_text: str) -> str | None`.

- [ ] **Step 1: Write failing test for TextCleaner**
Test stripping ruby tags (`[r]`, `\ruby{...}`, `[ruby=...]`), removing VN control codes, normalizing whitespace, deduplicating identical sentences within TTL, and debouncing typewriter character additions.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_text_cleaner.py -v`

- [ ] **Step 3: Implement TextCleaner**
Implement regex-based cleaner rules, time-based cache hash for deduplication, and prefix-growth typewriter detector.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_text_cleaner.py -v`

---

### Task 3: Glossary Manager & Context Buffer

**Files:**
- Create: `src/core/glossary.py`
- Create: `src/core/context_manager.py`
- Test: `tests/test_glossary.py`
- Test: `tests/test_context_manager.py`

**Interfaces:**
- Produces: `GlossaryManager` with `add_rule(src, target)`, `remove_rule(src)`, `apply_pre_rules(text)`, `format_prompt_instructions() -> str`.
- Produces: `ContextManager` with `add_turn(src, translated)`, `get_formatted_context(max_turns=4) -> str`, `clear()`.

- [ ] **Step 1: Write failing test for Glossary and ContextManager**
Test term substitution, character name mappings, prompt formatting, context ring buffer capacity, and history retrieval.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_glossary.py tests/test_context_manager.py -v`

- [ ] **Step 3: Implement GlossaryManager and ContextManager**
Implement case-sensitive/insensitive term mapping and a FIFO turn buffer formatted for LLM system prompts.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_glossary.py tests/test_context_manager.py -v`

---

### Task 4: Multi-Provider AI Translation Engine

**Files:**
- Create: `src/core/translator.py`
- Test: `tests/test_translator.py`

**Interfaces:**
- Consumes: `AppSettings`, `GlossaryManager`, `ContextManager`
- Produces: `AITranslator` class with async method `translate_stream(text: str, src_lang: str, tgt_lang: str, context: str, glossary_info: str) -> AsyncGenerator[str, None]`.

- [ ] **Step 1: Write failing test for AITranslator**
Mock HTTP responses for Google Gemini, OpenAI/DeepSeek (OpenAI-compatible), Claude, and verify streaming generator yields token chunks correctly and constructs proper system prompts.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_translator.py -v`

- [ ] **Step 3: Implement AITranslator**
Implement streaming API clients for:
  1. Google Gemini (`https://generativelanguage.googleapis.com/v1beta/models/...:streamGenerateContent`)
  2. OpenAI / DeepSeek / Groq / OpenRouter / Custom (`/v1/chat/completions` SSE stream)
  3. Anthropic Claude (`/v1/messages` SSE stream)
  4. Robust error handling (API key missing, rate limits, network timeout).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_translator.py -v`

---

### Task 5: Clipboard Listener & Named Pipe Hook Integration

**Files:**
- Create: `src/core/clipboard_listener.py`
- Test: `tests/test_clipboard_listener.py`

**Interfaces:**
- Produces: `ClipboardListener` (QObject / threading) emitting `text_captured = Signal(str)`.

- [ ] **Step 1: Write failing test for ClipboardListener**
Test signal emission when clipboard content changes, ignoring empty or non-text content.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_clipboard_listener.py -v`

- [ ] **Step 3: Implement ClipboardListener**
Implement clipboard polling and Windows clipboard listener events, with active/paused state control.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_clipboard_listener.py -v`

---

### Task 6: Screen Region OCR Capture Engine & Region Selector

**Files:**
- Create: `src/core/ocr_engine.py`
- Create: `src/ui/region_selector.py`
- Test: `tests/test_ocr_engine.py`

**Interfaces:**
- Produces: `OCREngine` with `recognize_region(bbox: tuple[int, int, int, int], lang: str) -> str`.
- Produces: `RegionSelectorDialog` (PySide6 semi-transparent fullscreen snip tool) emitting `region_selected = Signal(tuple)`.

- [ ] **Step 1: Write failing test for OCREngine**
Test image cropping, change-detection hash comparison, and OCR text extraction (with mock image fallback).

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_ocr_engine.py -v`

- [ ] **Step 3: Implement OCREngine & RegionSelectorDialog**
Integrate RapidOCR / fallback OCR engine with PIL screen capture (`ImageGrab`), plus an interactive Qt snip overlay tool.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_ocr_engine.py -v`

---

### Task 7: Edge-TTS Audio Engine & Global Hotkeys

**Files:**
- Create: `src/core/tts_player.py`
- Create: `src/core/hotkey_manager.py`
- Test: `tests/test_tts_player.py`

**Interfaces:**
- Produces: `TTSPlayer` with `play_voice(text: str, voice: str, rate: str)` and `stop()`.
- Produces: `GlobalHotkeyManager` with `register(hotkey_dict)` and Qt signal triggers.

- [ ] **Step 1: Write failing test for TTSPlayer & HotkeyManager**
Test voice generation queue and hotkey signal dispatching.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_tts_player.py -v`

- [ ] **Step 3: Implement TTSPlayer & GlobalHotkeyManager**
Implement async `edge-tts` stream player with pygame.mixer audio buffer, and `pynput` global key listener with Windows compatibility.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_tts_player.py -v`

---

### Task 8: Floating Subtitle Overlay Window (Glassmorphism & Click-through)

**Files:**
- Create: `src/ui/overlay_window.py`
- Test: `tests/test_overlay_window.py`

**Interfaces:**
- Produces: `OverlayWindow(QWidget)` with `update_text(source: str, translated: str, is_streaming: bool)`, `append_stream_chunk(chunk: str)`, `set_click_through(enabled: bool)`, `apply_style(font_family, font_size, text_color, outline_color, bg_opacity)`.

- [ ] **Step 1: Write unit test for OverlayWindow**
Test text streaming update, styling application, and geometry state persistence.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_overlay_window.py -v`

- [ ] **Step 3: Implement OverlayWindow**
Implement frameless, always-on-top, draggable subtitle window with customizable stroke/shadow text rendering (`QPainter` / RichText) and Windows `SetWindowLongPtr` click-through support.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_overlay_window.py -v`

---

### Task 9: Dialogue History / Backlog Window

**Files:**
- Create: `src/ui/backlog_window.py`
- Test: `tests/test_backlog_window.py`

**Interfaces:**
- Produces: `BacklogWindow(QWidget)` with `add_entry(timestamp, source_text, target_text, audio_replay_callback)`, `clear_history()`, `export_history(file_path)`.

- [ ] **Step 1: Write unit test for BacklogWindow**
Test item addition, search filter, export to text/json, and audio replay trigger.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_backlog_window.py -v`

- [ ] **Step 3: Implement BacklogWindow**
Implement modern QListWidget / QScrollArea with search input, copy buttons, replay TTS buttons, and export dialog.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_backlog_window.py -v`

---

### Task 10: Main Control Hub Window & Application Controller

**Files:**
- Create: `src/ui/main_window.py`
- Create: `src/app_controller.py`
- Create: `main.py`

**Interfaces:**
- Produces: Complete GUI application orchestrator wiring Input -> Preprocessing -> Translation -> Overlay & Backlog & TTS.

- [ ] **Step 1: Implement AppController**
Manage lifecycle, background worker threads (QThread / asyncio), coordinate signals between OCR/Clipboard, AI translation stream, TTS, and Overlay.

- [ ] **Step 2: Implement MainWindow (Modern Dark Glassmorphism UI)**
Build tabbed control hub:
  - Tab 1: Translation Controls (Start/Pause, Provider selector, Language Pair selector, Live status).
  - Tab 2: API Keys Management (Gemini, OpenAI, DeepSeek, Claude, Groq, OpenRouter, Custom URL).
  - Tab 3: Glossary / Name Mapping Table (Add, Edit, Delete, Import, Export).
  - Tab 4: Subtitle Appearance & Overlay Customization (Font picker, Color pickers, Opacity slider, Live preview).
  - Tab 5: TTS & Hotkeys Settings (Voice selection, Auto-read toggle, Keybinding editor).

- [ ] **Step 3: Implement main.py entrypoint**
Setup QApplication, high DPI scaling, dark theme stylesheet, and graceful shutdown handlers.

- [ ] **Step 4: Run manual and smoke test**
Launch main window and verify UI responsiveness and tab navigation.

---

### Task 11: End-to-End System Verification & Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration tests**
Test full pipeline: Simulated game text incoming -> Cleaner -> Glossary -> Mocked AI Translation streaming -> Overlay text update -> Backlog record.

- [ ] **Step 2: Run all tests in test suite**
Run: `pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 3: Launch and verify live interactive desktop app**
Run `python main.py` to confirm GUI displays cleanly without warnings or errors.
