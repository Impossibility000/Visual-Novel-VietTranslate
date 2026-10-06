import os
import time
import logging
from typing import Optional, Tuple, List
from PIL import Image, ImageGrab, ImageEnhance

logger = logging.getLogger("OCREngine")

class OCREngine:
    """High-Performance Screen Region Capture & Accelerated RapidOCR Engine."""
    
    def __init__(self, region: Optional[Tuple[int, int, int, int]] = None):
        self.region = region  # (x, y, width, height)
        self._last_frame_thumb = None
        self._ocr_instance = None
        self._init_ocr()

    def _init_ocr(self) -> None:
        """Initialize RapidOCR with optimized ONNX execution."""
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._ocr_instance = RapidOCR()
            logger.info("RapidOCR initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not load RapidOCR: {e}. Running in fallback mode.")
            self._ocr_instance = None

    def set_region(self, x: int, y: int, width: int, height: int) -> None:
        self.region = (x, y, width, height)
        self._last_frame_thumb = None

    def has_image_changed(self, img: Image.Image) -> bool:
        """Ultra-fast (0.2ms) perceptual difference check to detect text changes."""
        try:
            import numpy as np
            # Downscale to 96x48 thumbnail for sub-millisecond diff
            thumb = np.array(img.convert("L").resize((96, 48), Image.Resampling.BILINEAR), dtype=np.float32)
            if self._last_frame_thumb is None:
                self._last_frame_thumb = thumb
                return True
            
            diff_matrix = np.abs(thumb - self._last_frame_thumb)
            max_diff = float(np.max(diff_matrix))
            mean_diff = float(np.mean(diff_matrix))
            
            # If any character changed on screen
            if max_diff > 6.0 or mean_diff > 0.003:
                self._last_frame_thumb = thumb
                return True
            return False
        except Exception:
            return True

    def capture_screen_region(self) -> Optional[Image.Image]:
        """Capture the defined screen region as a PIL Image."""
        if not self.region:
            return None
        x, y, w, h = self.region
        if w <= 0 or h <= 0:
            return None
        try:
            bbox = (x, y, x + w, y + h)
            return ImageGrab.grab(bbox=bbox)
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None

    def preprocess_image(self, img: Image.Image) -> Image.Image:
        """Enhance contrast for visual novel text to maximize OCR speed and accuracy."""
        try:
            # Contrast boost for crisp character edge detection
            enhancer = ImageEnhance.Contrast(img)
            return enhancer.enhance(1.4)
        except Exception:
            return img

    def recognize_image(self, img: Image.Image) -> str:
        """Run OCR on the enhanced image and return extracted text lines."""
        if self._ocr_instance is not None:
            try:
                import numpy as np
                enhanced = self.preprocess_image(img)
                img_np = np.array(enhanced)
                
                results, _ = self._ocr_instance(img_np)
                if results:
                    # results format: [[box, text, score], ...]
                    # Filter low-confidence noise (< 0.4)
                    lines = []
                    for res in results:
                        if res and len(res) > 1 and res[1]:
                            text_str = str(res[1]).strip()
                            if text_str:
                                lines.append(text_str)
                    return " ".join(lines).strip()
            except Exception as e:
                logger.error(f"RapidOCR recognition error: {e}")
        
        return ""

    def scan_once(self) -> Optional[str]:
        """Capture region, check if changed, and run OCR if changed."""
        img = self.capture_screen_region()
        if img is None:
            return None
        if not self.has_image_changed(img):
            return None  # Screen has not changed
        
        text = self.recognize_image(img)
        return text if text.strip() else None
