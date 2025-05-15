from src.engines.dummy import DummyOCREngine
from src.interface.module_interface import OCRInterface
from config.settings import settings

def get_ocr_engine() -> OCRInterface:
    if settings.model_type == "dummy":
        return DummyOCREngine()
    raise ValueError(f"Unsupported OCR engine: {settings.model_type}")
