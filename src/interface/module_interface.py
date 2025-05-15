from typing import Tuple, List, Dict
from PIL import Image
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Result:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]


class OCRInterface(ABC):
    @abstractmethod
    def run_ocr(self, image: Image.Image) -> List[Result]:
        pass


class VLMInterface(ABC):
    @abstractmethod
    def run_vlm(self, image: Image.Image) -> Dict:
        """Extracts structured information from a document image."""
        pass
