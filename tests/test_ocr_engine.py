import unittest
from unittest.mock import MagicMock
from PIL import Image, ImageDraw
from src.core.ocr_engine import OCREngine

class TestOCREngine(unittest.TestCase):
    def test_ocr_engine_initialization(self):
        engine = OCREngine()
        self.assertTrue(engine.region is None or isinstance(engine.region, tuple))

    def test_frame_change_detection(self):
        engine = OCREngine()
        
        img1 = Image.new("RGB", (100, 50), color="white")
        img2 = Image.new("RGB", (100, 50), color="white")
        img3 = Image.new("RGB", (100, 50), color="black")
        
        self.assertTrue(engine.has_image_changed(img1))
        self.assertFalse(engine.has_image_changed(img2))
        self.assertTrue(engine.has_image_changed(img3))

if __name__ == "__main__":
    unittest.main()
