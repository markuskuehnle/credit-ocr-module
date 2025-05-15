from PIL import Image
from src.engines.dummy import DummyOCREngine

def test_dummy_ocr():
    engine = DummyOCREngine()
    image = Image.new("RGB", (200, 100), color="white")
    results = engine.run_ocr(image)

    assert len(results) == 2
    assert results[0].text == "Hello"
    assert results[1].bbox == (10, 50, 120, 70)
