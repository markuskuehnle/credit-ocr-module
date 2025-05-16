import base64, io, os
from typing import List
from PIL import Image
import ollama

from src.interface.module_interface import Result   # your dataclass

_SYSTEM_PROMPT = (
    "Extract only the visible, human-readable text from the image. "
    "Return raw text lines in reading order – no commentary."
)

class GemmaOCREngine:
    def __init__(self, model: str | None = None, temp: float = 0.0):
        self.model = model or os.getenv("GEMMA_MODEL", "llava-phi3:3.8b") # gemma3.1b
        self.temp  = temp

    def _b64(self, img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def run_ocr(self, img: Image.Image) -> List[Result]:
        resp = ollama.generate(
            model=self.model,
            prompt=_SYSTEM_PROMPT,
            images=[self._b64(img)],
            options={"temperature": self.temp},
        )["response"]

        # Gemma doesn’t give bboxes; wrap entire page in one.
        return [Result(text=resp.strip(),
                       confidence=0.5,
                       bbox=[0, 0, img.width, img.height])]
