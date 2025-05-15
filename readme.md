# OCR Module

This is a standalone OCR microservice designed to run as a container.

![mvp](images/ocr_system_architecture_diagram_simplified.jpeg)

## Architecture

- Exposes a FastAPI service
- Accepts image uploads for OCR
- Returns structured OCR results
- Designed with a pluggable engine interface

## Interfaces

- Module Input: file folder with multiple images (pages as .png)
- OCR Input: `image/png` (one single page) for OCR
- Output: JSON containing OCR text, bounding boxes, and confidence scores.

## Prerequisites

Before using this project, make sure you have the following installed:

### Required

- **Docker Desktop**
  - [Install Guide](https://docs.docker.com/)

- Docker daemon running (test with `docker info`)

### Optional (for testing locally without Docker)

- Python 3.10+ (if you want to run tests manually)
- `poppler-utils` and dependencies for `pdf2image`

## Development

### 1. Build the Docker image

```bash
docker build --no-cache -t ocr-module .
```

### 2. Run the **FastAPI server** (default)

This uses `uvicorn` to start the API (based on `ENTRYPOINT` in your Dockerfile):

```bash
docker run --rm -p 8080:8080 ocr-module
```

You can now `POST` a PNG to:

* `http://localhost:8080/ocr/` → for OCR
* `http://localhost:8080/vlm_extract/` → for dummy VLM (if enabled)
* `http://localhost:8080/health` → health check

## 3. Run the **local test runner** (from PDF to JSON)

> This bypasses the FastAPI app and runs `tests/local_test.py`, with mounted input/output folders under `tmp/`.

**Required:**

* A PDF must be placed in `tmp/input_pdf/` before running.
* The container will convert PDF to PNGs and output JSONs to `tmp/output/`.

**Command:**

```bash
docker run --rm \
  -v "$PWD/tmp:/app/tmp" \
  -e PYTHONPATH=/app \
  -e RUN_LOCAL_TEST=1 \
  --entrypoint python \
  ocr-module \
  tests/local_test.py
```

### What this setup gives you

| Use Case       | Command                                                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Run API server | `docker run --rm -p 8080:8080 ocr-module`                                                                                          |
| Run local test | `docker run --rm -v "$PWD/tmp:/app/tmp" -e PYTHONPATH=/app -e RUN_LOCAL_TEST=1 --entrypoint python ocr-module tests/local_test.py` |

Let me know if you want to define a Makefile or Docker Compose for this – but as-is, you’re clean.

