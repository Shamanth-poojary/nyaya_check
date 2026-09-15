import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes import check, ocr

app = FastAPI(
    title="Legal Metrology OCR / Extraction Service",
    description=(
        "Independent image-intelligence microservice that turns packaged-"
        "commodity images into structured, compliance-ready evidence for the "
        "downstream Legal Metrology rules engine."
    ),
    version="0.1.0",
)

app.include_router(ocr.router)
app.include_router(check.router)

# Serve static UI files (index.html camera/upload page)
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    """Serve the OCR capture/upload UI at the root URL."""
    return FileResponse(os.path.join(_static_dir, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}
