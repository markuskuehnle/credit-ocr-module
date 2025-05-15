from typing import List
from PIL import Image
from src.interface.module_interface import OCRInterface, Result

class DummyOCREngine(OCRInterface):
    def run_ocr(self, image: Image.Image) -> List[Result]:
        return [
            Result(text="World", confidence=0.95, bbox=(10, 50, 120, 70)),
        ]
