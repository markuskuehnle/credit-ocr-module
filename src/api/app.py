from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
from factory.factory import get_ocr_engine

app = FastAPI()
engine = get_ocr_engine()

@app.post("/ocr/")
async def run_ocr(file: UploadFile = File(...)):
    if file.content_type != "image/png":
        return JSONResponse(status_code=400, content={"detail": "Only PNG supported"})

    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    results = engine.run_ocr(image)
    return [
        {"text": r.text, "confidence": r.confidence, "bbox": r.bbox}
        for r in results
    ]


@app.get("/health")
def health_check():
    return {"status": "ok"}
