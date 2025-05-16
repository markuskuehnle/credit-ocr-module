import os
import logging
import json
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path

from src.factory.factory import get_ocr_engine
from src.interface.module_interface import Result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INPUT_PDF_DIR = Path("tmp/input_pdf")
IMAGE_OUTPUT_BASE = Path("tmp/data")
OUTPUT_ROOT = Path("tmp/output")


def convert_pdf_to_images(pdf_path: Path, out_dir: Path):
    if out_dir.exists() and any(out_dir.glob("*.png")):
        logger.info(f"Skipping conversion. PNGs already exist in {out_dir}")
        return

    logger.info(f"Converting PDF: {pdf_path.name} to PNGs...")
    out_dir.mkdir(parents=True, exist_ok=True)
    images = convert_from_path(str(pdf_path))
    for i, img in enumerate(images):
        img.save(out_dir / f"page_{i:02}.png")
    logger.info(f"Saved {len(images)} pages to {out_dir}")


def process_document_folder(doc_path: Path, output_path: Path):
    logger.info(f"OCR processing: {doc_path.name}")
    ocr_engine = get_ocr_engine()
    output_path.mkdir(parents=True, exist_ok=True)
    
    page_images = sorted(doc_path.glob("*.png"))
    if not page_images:
        logger.warning(f"No PNGs found in {doc_path}")
        return

    for page in page_images:
        logger.info(f"file={page.name} ({page})")
        try:
            image   = Image.open(page)
            results = ocr_engine.run_ocr(image)
        except Exception as e:
            logger.error(f"Error processing {page.name}: {e}")
            continue

        ocr_payload = [
            {"text": r.text, "confidence": r.confidence, "bbox": r.bbox}
            for r in results
        ]
        out_file = output_path / f"{page.stem}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(ocr_payload, f, indent=2)
        logger.info(f"Written: {out_file}")


def run_local_ocr_pipeline():
    if os.getenv("RUN_LOCAL_TEST") != "1":
        logger.warning("Local test runner skipped. Set RUN_LOCAL_TEST=1 to enable.")
        return

    if not INPUT_PDF_DIR.exists():
        logger.error(f"Missing input dir: {INPUT_PDF_DIR}")
        return

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    IMAGE_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    pdf_files = list(INPUT_PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {INPUT_PDF_DIR}")
        return

    for pdf in pdf_files:
        stem = pdf.stem.lower().replace(" ", "_")
        image_dir = IMAGE_OUTPUT_BASE / stem
        output_dir = OUTPUT_ROOT / stem

        convert_pdf_to_images(pdf, image_dir)
        process_document_folder(image_dir, output_dir)


if __name__ == "__main__":
    run_local_ocr_pipeline()
