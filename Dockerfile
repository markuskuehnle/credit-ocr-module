FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install Poppler and required build tools
RUN apt-get update && \
    apt-get install -y poppler-utils gcc libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean

ENV PYTHONPATH=/app/src

# Default: API server
ENTRYPOINT ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
