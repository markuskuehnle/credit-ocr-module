"""
Generic PDF-or-Image → JSON OCR runner.

Usage:
    process_input(Path("foo.pdf"), image_base_directory, json_output_root)
    process_input(Path("bar.png"), image_base_directory, json_output_root)
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List

import camelot
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path

from src.factory.factory import get_ocr_engine
from src.interface.module_interface import Result

# ── logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(asctime)s:%(message)s",
    datefmt="%H:%M:%S",
)
log: logging.Logger = logging.getLogger("generic_ocr")

# ── repository paths (relative; keep them project-agnostic) ────────────────
REPOSITORY_ROOT: Path = Path(__file__).resolve().parents[1]
TMP_ROOT:        Path = REPOSITORY_ROOT / "tmp"

INPUT_DIRECTORY:   Path = TMP_ROOT / "input"   # now unified
IMAGE_DIRECTORY:   Path = TMP_ROOT / "data"
JSON_DIRECTORY:    Path = TMP_ROOT / "output"

# ── helper to render a single PDF page ─────────────────────────────────────
def render_page_to_png(
    pdf_path: Path,
    page_index: int,
    image_directory: Path,
    dpi: int = 150,
) -> Path:
    png_path = image_directory / f"page_{page_index:02}.png"
    if png_path.exists():
        return png_path
    image_directory.mkdir(parents=True, exist_ok=True)
    img = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=page_index + 1,
        last_page=page_index + 1,
    )[0]
    img.save(png_path)
    return png_path

# ── wrap PDF text+tables into one Result ──────────────────────────────────
def result_from_native_layer(
    pdf_page,
    *,
    tables: List[list],
    page_index: int
) -> List[Result]:
    payload = {"text": (pdf_page.extract_text() or "").strip(), "tables": tables}
    return [
        Result(
            text=json.dumps(payload, ensure_ascii=False),
            confidence=1.0,
            bbox=(0, 0, int(pdf_page.width), int(pdf_page.height)),
            page_index=page_index,
            block_id=f"p{page_index}_b0",
        )
    ]

# ── existing PDF pipeline ──────────────────────────────────────────────────
def process_document(
    pdf_path: Path,
    *,
    image_base_directory: Path = IMAGE_DIRECTORY,
    json_output_root: Path = JSON_DIRECTORY,
) -> None:
    stem = pdf_path.stem.lower().replace(" ", "_")
    img_dir = image_base_directory / stem
    out_dir = json_output_root / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = get_ocr_engine()
    log.info("Starting PDF %s with engine %s", pdf_path.name, engine.__class__.__name__)

    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        native_count = ocr_count = 0

        for page_index in range(total_pages):
            page_json_path = out_dir / f"page_{page_index:02}.json"
            if page_json_path.exists():
                continue

            pdf_page = pdf.pages[page_index]
            text = (pdf_page.extract_text() or "").strip()
            if text:
                # native layer
                tables = [
                    t.df.values.tolist()
                    for t in camelot.read_pdf(
                        str(pdf_path),
                        pages=str(page_index+1),
                        flavor="stream"
                    )
                ]
                results = result_from_native_layer(pdf_page, tables=tables, page_index=page_index)
                native_count += 1
                source = "PDF"
            else:
                # OCR fallback
                ocr_count += 1
                png = render_page_to_png(pdf_path, page_index, img_dir)
                with Image.open(png) as im:
                    im.thumbnail((1024,1024))
                    start = time.perf_counter()
                    results = engine.run_ocr(im)
                    dur = time.perf_counter() - start
                for idx, r in enumerate(results):
                    r.page_index = page_index
                    r.block_id   = f"p{page_index}_b{idx}"
                source = engine.__class__.__name__

            # assemble page JSON
            w,h = int(pdf_page.width), int(pdf_page.height)
            payload = {
                "schema_version": "1.0",
                "page": page_index,
                "size": {"width": w, "height": h},
                "items": [r.__dict__ for r in results]
            }
            page_json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
            log.info("Page %02d (%s) → %s", page_index, source, page_json_path.name)

    log.info("PDF %s done: %d native, %d OCR", pdf_path.name, native_count, ocr_count)

# ── NEW: single entry for PDF **or** image ─────────────────────────────────
def process_input(
    input_path: Path,
    *,
    image_base_directory: Path = IMAGE_DIRECTORY,
    json_output_root:  Path = JSON_DIRECTORY,
) -> None:
    """
    Accepts a PDF (multi-page) or a single image (PNG/JPG).  
    Writes tmp/output/<stem>/page_00.json (and more for PDFs).
    """
    suffix = input_path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg"):
        stem = input_path.stem.lower().replace(" ", "_")
        out_dir = json_output_root / stem
        out_dir.mkdir(parents=True, exist_ok=True)

        engine = get_ocr_engine()
        log.info("Starting Image %s with engine %s", input_path.name, engine.__class__.__name__)

        with Image.open(input_path) as im:
            im.thumbnail((1024,1024))
            start = time.perf_counter()
            results = engine.run_ocr(im)
            dur = time.perf_counter() - start

        # single‐page JSON
        w,h = im.width, im.height
        for idx, r in enumerate(results):
            r.page_index = 0
            r.block_id   = f"p0_b{idx}"

        payload = {
            "schema_version": "1.0",
            "page": 0,
            "size": {"width": w, "height": h},
            "items": [r.__dict__ for r in results]
        }
        out_file = out_dir / "page_00.json"
        out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        log.info("Image → %s (%.1fs)", out_file.name, dur)

    elif suffix == ".pdf":
        process_document(
            input_path,
            image_base_directory=image_base_directory,
            json_output_root=json_output_root
        )
    else:
        log.warning("Skipping unsupported file type: %s", input_path)

# ── CLI wrapper for local tests ─────────────────────────────────────────────
def run_local_ocr_pipeline() -> None:
    if os.getenv("RUN_LOCAL_TEST") != "1":
        log.warning("RUN_LOCAL_TEST != '1' – skipping")
        return
    for path in INPUT_DIRECTORY.glob("*"):
        process_input(path)

if __name__ == "__main__":
    run_local_ocr_pipeline()
