from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import tempfile
import os
import json
import time

from PIL import Image
import pdfplumber

from factory.factory import get_ocr_engine
from src.interface.module_interface import Result

app = FastAPI(title="Generic OCR Service", version="1.1.0")
ocr_engine = get_ocr_engine()


def _build_page_payload(
    results: List[Result],
    page_index: int,
    width: int,
    height: int,
) -> Dict[str, Any]:
    """
    Assemble JSON payload for one page or image.
    """
    items: List[Dict[str, Any]] = []
    for idx, res in enumerate(results):
        items.append({
            "block_id": f"p{page_index}_b{idx}",
            "text": res.text,
            "confidence": res.confidence,
            "bbox": res.bbox,
        })
    return {
        "schema_version": "1.0",
        "page": page_index,
        "size": {"width": width, "height": height},
        "items": items,
    }


@app.post("/ocr", response_model=List[Dict[str, Any]])
async def ocr_endpoint(file: UploadFile = File(...)):
    """
    Accept a PDF or an image (PNG/JPG). Returns a list of page payloads.
    - PDF: one payload per page.
    - Image: single payload with page_index=0.
    """
    content_type = file.content_type.lower()

    # handle PDF
    if content_type == "application/pdf":
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        data = await file.read()
        tmp.write(data); tmp.flush(); tmp.close()
        try:
            pages: List[Dict[str, Any]] = []
            with pdfplumber.open(tmp.name) as pdf_doc:
                for page_index, pdf_page in enumerate(pdf_doc.pages):
                    width, height = int(pdf_page.width), int(pdf_page.height)
                    text = (pdf_page.extract_text() or "").strip()

                    if text:
                        # native text layer
                        results = [Result(text=text, confidence=1.0, bbox=(0,0,width,height))]
                    else:
                        # fall back to OCR on downscaled image
                        img = pdf_page.to_image(resolution=150).original
                        img.thumbnail((1024, 1024))
                        results = ocr_engine.run_ocr(img)

                    pages.append(_build_page_payload(results, page_index, width, height))
            return JSONResponse(content=pages)

        finally:
            os.unlink(tmp.name)

    # handle images
    elif content_type in ("image/png", "image/jpeg", "image/jpg"):
        data = await file.read()
        try:
            img = Image.open(io.BytesIO(data))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        width, height = img.size
        results = ocr_engine.run_ocr(img)
        payload = _build_page_payload(results, page_index=0, width=width, height=height)
        return JSONResponse(content=[payload])

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or PNG/JPG.")


@app.get("/health")
def health_check():
    return {"status": "ok"}
