# src/engines/smolvlm_ocr.py
import accelerate                          # must import first
import importlib, transformers
importlib.reload(transformers)             # re-evaluate accelerate check

import torch, json
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText
from typing import List
from src.interface.module_interface import Result, OCRInterface

_PROMPT = (
    "Extract all readable text from this image in natural reading order. "
    "No commentary."
)

class SmolVLMEngine(OCRInterface):
    def __init__(self,
                 model_name: str = "HuggingFaceTB/SmolVLM-Instruct",
                 max_tokens: int = 256):
        self.device  = "cuda" if torch.cuda.is_available() else (
                       "mps"  if torch.backends.mps.is_available() else "cpu")
        self.proc    = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        self.model.to(self.device)                # move to gpu/mps/cpu
        self.max_tok = max_tokens

    @torch.inference_mode()
    def run_ocr(self, img: Image.Image) -> List[Result]:
        inputs  = self.proc(text=_PROMPT, images=img, return_tensors="pt").to(self.device)
        ids     = self.model.generate(**inputs, max_new_tokens=self.max_tok)
        out_txt = self.proc.batch_decode(ids, skip_special_tokens=True)[0].strip()
        return [Result(text=out_txt, confidence=0.5,
                       bbox=[0, 0, img.width, img.height])]
