"""
app/main.py — Primary application entry point for the Legal Metrology microservice.

Features:
- Versioned API under /v1 (/v1/extract, /v1/extract/multi, /v1/check, /v1/health, /v1/ready)
- API key authentication toggle via Settings.api_key
- Configurable CORS middleware for teammate frontend origins
- Structured request logging and latency instrumentation
- OpenAPI documentation polish with realistic examples
"""

import logging
import os
import time

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import verify_api_key
from app.config import settings
from app.routes import check, health, ocr

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Legal Metrology OCR & Compliance Verification Service",
    description=(
        "Production-grade microservice for Legal Metrology compliance verification. "
        "Transforms packaging photos into structured, compliance-ready evidence and executes "
        "statutory verification against the Legal Metrology (Packaged Commodities) Rules, 2011.\n\n"
        "### API Versioning\n"
        "All endpoints are versioned under `/v1`. This represents the stable, production-ready contract.\n\n"
        "### Authentication\n"
        "When authentication is enabled in `Settings` (`API_KEY`), all `/v1/*` endpoints except "
        "`/v1/health` and `/v1/ready` require an `X-API-Key` header."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware configuration
if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Request timing & access logging middleware
@app.middleware("http")
async def log_and_time_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{duration:.3f}s"
    logger.info(
        "%s %s -> status=%d duration=%.3fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# Friendly validation error handler for file uploads (e.g. from Swagger UI)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for err in exc.errors():
        if err.get("type") == "value_error" and "Expected UploadFile" in str(err.get("msg", "")):
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "No image uploaded. Please select a valid image file (JPEG, PNG, or WebP) before submitting."
                },
            )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# --- v1 Stable Versioned API Router ---
v1_router = APIRouter(prefix="/v1")

# Health & readiness (unauthenticated)
v1_router.include_router(health.router)

# Core OCR & Extraction (secured by API key if configured)
v1_router.include_router(
    ocr.router,
    dependencies=[Depends(verify_api_key)],
)

# End-to-end Compliance Evaluation (secured by API key if configured)
v1_router.include_router(
    check.router,
    dependencies=[Depends(verify_api_key)],
)

app.include_router(v1_router)

# --- Backward compatibility aliases (unversioned routes) ---
# Kept without polluting schema to support existing scripts and tests during rollout
legacy_router = APIRouter(include_in_schema=False)
legacy_router.include_router(health.router)
legacy_router.include_router(ocr.router, dependencies=[Depends(verify_api_key)])
legacy_router.include_router(check.router, dependencies=[Depends(verify_api_key)])
app.include_router(legacy_router)


# --- Static Web UI ---
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    """Serve the OCR capture/upload UI at the root URL."""
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Legal Metrology OCR Service. Visit /docs for API documentation."}
