from src.interface.module_interface import OCRInterface
from config.settings import settings

def get_ocr_engine() -> OCRInterface:
    if settings.model_type == "dummy":
        from src.engines.dummy import DummyOCREngine
        return DummyOCREngine()
    elif settings.model_type == "gemma":
        from src.engines.gemma_ocr import GemmaOCREngine
        return GemmaOCREngine()
    raise ValueError(f"Unsupported OCR engine: {settings.model_type}")
