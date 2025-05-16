from PIL import Image
from pathlib import Path
from src.factory.factory import get_ocr_engine

def run_ocr(file_path: Path):
    image = Image.open(file_path)
    engine = get_ocr_engine()
    return engine.run_ocr(image)
