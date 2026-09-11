from fastapi import FastAPI

from app.routes import ocr

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


@app.get("/health")
def health():
    return {"status": "ok"}
