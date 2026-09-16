"""
app/routes/health.py — Health and Readiness check endpoints.

Exposes:
  GET /health (and /v1/health) — Liveness check
  GET /ready  (and /v1/ready)  — Readiness check (verifies PaddleOCR model status)
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ocr.paddle import is_engine_initialized

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service liveness status", examples=["ok"])


class ReadinessResponse(BaseModel):
    status: str = Field(default="ready", description="Service readiness status", examples=["ready"])
    engine: str = Field(default="paddleocr", description="Underlying OCR engine", examples=["paddleocr"])
    modelLoaded: bool = Field(
        description="Whether the OCR model weights have finished loading into memory",
        examples=[True],
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns HTTP 200 with status='ok' when the application process is running and accepting HTTP requests.",
)
def health():
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Confirms whether the OCR inference engine is initialized and ready to serve extraction traffic.",
)
def ready():
    loaded = is_engine_initialized()
    return ReadinessResponse(
        status="ready" if loaded else "initializing",
        engine="paddleocr",
        modelLoaded=loaded,
    )
