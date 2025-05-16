import io, json, camelot, layoutparser as lp, pdfplumber
from typing import List, Dict
from PIL import Image
from paddleocr import PaddleOCR
from pathlib import Path
from src.interface.module_interface import Result, OCRInterface

ocr = PaddleOCR(use_angle_cls=True, lang='en')
model = lp.Detectron2LayoutModel(
    "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "text", 1: "title", 2: "list", 3: "table", 4: "figure"},
)

def extract_scanned(img: Image.Image) -> Dict:
    layout = model.detect(img)
    text_blocks, tables = [], []
    for block in layout:
        crop = img.crop(block.coordinates)
        if block.type == "table":
            buf = io.BytesIO(); crop.save(buf, format="PNG")
            tmp = "/tmp/table.png"; Path(tmp).write_bytes(buf.getvalue())
            df = camelot.read_pdf(tmp, flavor="lattice")[0].df
            tables.append({"bbox": block.coordinates, "data": df.values.tolist()})
        else:
            res  = ocr.ocr(crop, cls=True)
            line = " ".join(r[1][0] for r in res)
            text_blocks.append(line)
    return {"text": "\n".join(text_blocks), "tables": tables}

class HybridOCREngine(OCRInterface):
    """
    Returns ONE Result object whose .text field is the JSON string
    containing 'text' and 'tables'.  This keeps the existing pipeline
    unchanged (we’ll detect JSON downstream).
    """
    def run_ocr(self, img: Image.Image) -> List[Result]:
        payload = extract_scanned(img)
        return [Result(text=json.dumps(payload, ensure_ascii=False),
                       confidence=1.0,
                       bbox=[0, 0, img.width, img.height])]
