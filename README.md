# AetherVN - Realtime AI Visual Novel & Screen Translator 🎮✨

Ứng dụng dịch thuật Visual Novel, Game và Ứng dụng Desktop theo thời gian thực sử dụng các mô hình AI tiên tiến nhất (Google Gemini, OpenAI GPT-4o, DeepSeek, Anthropic Claude, Groq, OpenRouter).

---

## 🌟 Tính Năng Nổi Bật

1. **Cơ chế Bắt Chữ Kép (Dual Capture)**:
   - **Chính**: Bắt tự động qua luồng sao chép Clipboard (tương thích 100% với Textractor, Visual Novel Reader, hoặc các công cụ Hook RAM khác).
   - **Phụ trợ**: Tích hợp Screen Region OCR quét trực tiếp vùng hộp thoại game trên màn hình với thuật toán phát hiện thay đổi khung hình (Frame-diff check) giúp tiết kiệm tài nguyên.
2. **Hỗ trợ Đa dạng Nhà cung cấp AI**:
   - **Google Gemini**: Hỗ trợ `gemini-2.5-flash`, `gemini-2.0-flash` (Tốc độ phản hồi cực nhanh < 350ms, dịch văn phong tiếng Nhật/Việt tự nhiên).
   - **OpenAI & DeepSeek**: `gpt-4o-mini`, `gpt-4o`, `deepseek-chat` (DeepSeek-V3, R1).
   - **Anthropic Claude**: `claude-3-5-haiku`, `claude-3-5-sonnet`.
   - **Groq / OpenRouter / Custom Endpoint**: Dùng được cả mô hình LLM chạy cục bộ (Ollama, LM Studio, vLLM).
3. **Phụ Đề Nổi Trong Suốt (Floating Glassmorphism Overlay)**:
   - Cửa sổ phụ đề Always-On-Top, trong suốt, viền bóng chữ sắc nét chống chói lóa trên mọi khung cảnh game.
   - Chế độ **Click-Through (`Ctrl + F1`)**: Cho phép click chuột xuyên qua khung phụ đề để tương tác với game mà không bị cản trở.
   - Hỗ trợ **Streaming Display**: Hiển thị từng chữ ngay khi AI sinh từ theo thời gian thực.
4. **Bộ nhớ Ngữ Cảnh (Context Memory) & Quản lý Từ Điển (Glossary)**:
   - Lưu 3–5 câu thoại gần nhất để AI hiểu mạch truyện, giữ đúng đại từ xưng hô theo ngữ cảnh.
   - Bảng quy tắc từ điển và danh xưng nhân vật tùy chỉnh (Ví dụ: `先輩` -> `Tiền bối`, `俺` -> `Tôi`).
5. **Dọn dẹp Chuỗi & Lọc Typewriter (Text Cleaner)**:
   - Tự động bóc tách mã ruby, furigana (`[わたし]`, `{瞳|ひとみ}`), escape codes và khử trùng lặp câu khi game gõ từng ký tự.
6. **Lịch sử Hội Thoại (Backlog)**:
   - Xem lại toàn bộ câu thoại gốc và bản dịch, tìm kiếm từ khóa, sao chép hoặc xuất ra file `.txt` / `.json`.
7. **Giọng Đọc AI (Edge-TTS)**:
   - Tích hợp Microsoft Edge-TTS giọng đọc tự nhiên (tiếng Việt Hoài My/Nam Minh, tiếng Nhật Nanami/Keita) miễn phí.
8. **Hệ thống Phím Tắt Toàn Cục (Global Hotkeys)**:
   - `Ctrl + F1`: Bật/Tắt chế độ Click-through của khung phụ đề.
   - `Ctrl + F2`: Tạm dừng / Tiếp tục dịch.
   - `Ctrl + F3`: Kéo chuột chọn vùng OCR mới trên màn hình.
   - `Ctrl + F4`: Ẩn / Hiện nhanh khung phụ đề.
   - `Ctrl + F5`: Đọc lại câu thoại vừa dịch.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

### 2. Khởi chạy ứng dụng:
```bash
python main.py
```

---

## 📖 Hướng Dẫn Kết Nối Game (Visual Novel)

### Cách 1: Sử dụng chung với Textractor (Khuyên dùng - Độ chính xác 100%)
1. Mở game Visual Novel của bạn.
2. Mở **Textractor**, bấm `Attach to game` và chọn tiến trình game.
3. Trong danh sách hook của Textractor, chọn đúng dòng thoại của nhân vật và thêm extension **Copy to Clipboard**.
4. Mở **AetherVN**, bấm **▶ Bắt Đầu Dịch**. Phụ đề tiếng Việt sẽ tự động xuất hiện trên màn hình mỗi khi nhân vật trong game nói!
5. Nhấn `Ctrl + F1` để khóa click-through và đặt khung phụ đề đè lên hộp thoại game.

### Cách 2: Sử dụng OCR Quét Vùng Màn Hình
1. Mở **AetherVN**, tích chọn `Bật OCR quét vùng màn hình`.
2. Bấm nút `📐 Kéo chọn vùng OCR (Ctrl+F3)`.
3. Dùng chuột kéo quét một hình chữ nhật bao quanh khung thoại của game.
4. Ứng dụng sẽ tự động chụp và dịch mỗi khi câu thoại trên màn hình thay đổi.
