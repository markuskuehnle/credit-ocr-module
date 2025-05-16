from src.interface.module_interface import OCRInterface
from config.settings import settings

def get_ocr_engine() -> OCRInterface:
    if settings.model_type == "dummy":
        from src.engines.dummy import DummyOCREngine
        return DummyOCREngine()
    elif settings.model_type == "gemma":
        from src.engines.gemma_ocr import GemmaOCREngine
        return GemmaOCREngine()
    elif settings.model_type == "hybrid":
        from src.engines.hybrid_ocr import HybridOCREngine
        return HybridOCREngine()
    elif settings.model_type == "smolvlm":
        from src.engines.smolvlm_ocr import SmolVLMEngine
        return SmolVLMEngine()
    raise ValueError(f"Unsupported OCR engine: {settings.model_type}")
