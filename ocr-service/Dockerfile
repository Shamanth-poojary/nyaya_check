# Multi-stage Dockerfile for Legal Metrology OCR / Extraction Service
# Optimized for Python 3.13, pre-baked PaddleOCR weights, and Gunicorn+Uvicorn concurrency.

# ------------------------------------------------------------------------------
# Stage 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a standalone target directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Minimal Runtime
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

WORKDIR /app

# System dependencies for OpenCV headless and PaddlePaddle CPU runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Setup non-root app user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /home/appuser/.paddleocr /home/appuser/.paddle && \
    chown -R appuser:appuser /app /home/appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/appuser \
    PADDLE_HOME=/home/appuser/.paddleocr \
    PORT=8000 \
    WEB_CONCURRENCY=2

# Copy application source code
COPY --chown=appuser:appuser . /app

# Pre-download and bake PaddleOCR model weights into the image at build time.
# Prevents the 30-70s first-request cold start penalty in production.
USER appuser
RUN python -c "from app.ocr.paddle import warmup_engine; warmup_engine(); print('PaddleOCR models successfully baked into image')"

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Production runner with Gunicorn managing Uvicorn workers
CMD ["sh", "-c", "gunicorn app.main:app -w ${WEB_CONCURRENCY:-2} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} --timeout 120 --access-logfile -"]
