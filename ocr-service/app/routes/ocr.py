import io
import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.ocr.paddle import run_ocr
from app.schemas.response import BoundingBox, ExtractionResponse, RawOCRLine, empty_response

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 15


@router.post("/extract", response_model=ExtractionResponse)
async def extract(image: UploadFile = File(...)) -> ExtractionResponse:
    """
    Phase 1: validate the upload and return a well-formed placeholder JSON.

    Later phases wire in, in order:
      Phase 3 - OpenCV preprocessing
      Phase 2 - PaddleOCR (raw text + bbox + confidence)
      Phase 4 - OCR normalization
      Phase 5/6/7 - Regex + keyword + NER classification, commodity category
      Phase 8 - Visual analysis
      Phase 9 - Evidence assembly (raw OCR, confidence, crops)
    """
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type: {image.content_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    contents = await image.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large ({size_mb:.1f} MB > {MAX_FILE_SIZE_MB} MB limit)",
        )

    try:
        pil_image = Image.open(io.BytesIO(contents))
        pil_image.verify()
        pil_image = Image.open(io.BytesIO(contents))  # reopen: verify() closes it
        width, height = pil_image.size
    except Exception:
        raise HTTPException(status_code=400, detail="File is not a valid image")

    response = empty_response(image_id=image.filename or "unknown", width=width, height=height)

    # Phase 2: run PaddleOCR and populate rawOCR only. Classification into
    # named fields (MRP, net qty, dates, etc.) happens in later phases.
    #
    # Downscale large photos before OCR -- inference time scales with pixel
    # count, and phone photos are often much bigger than needed for text
    # detection. Bounding boxes come back in the resized image's coordinate
    # space, so we scale them back up to match the ORIGINAL width/height
    # reported in `document`, keeping bboxes consistent for downstream
    # spatial rules (Rules 7-10).
    MAX_DIMENSION = 1600
    longest_side = max(width, height)
    scale = 1.0
    ocr_image = pil_image
    if longest_side > MAX_DIMENSION:
        scale = MAX_DIMENSION / longest_side
        new_size = (round(width * scale), round(height * scale))
        ocr_image = pil_image.resize(new_size, Image.LANCZOS)

    suffix = os.path.splitext(image.filename or "")[1] or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            ocr_image.convert("RGB").save(tmp, format="JPEG", quality=92)
            tmp_path = tmp.name

        lines = run_ocr(tmp_path)
        inverse_scale = 1.0 / scale  # 1.0 if we didn't resize
        response.rawOCR = [
            RawOCRLine(
                text=line.text,
                bbox=BoundingBox(
                    xmin=round(line.bbox[0] * inverse_scale),
                    ymin=round(line.bbox[1] * inverse_scale),
                    xmax=round(line.bbox[2] * inverse_scale),
                    ymax=round(line.bbox[3] * inverse_scale),
                ),
                confidence=line.confidence,
            )
            for line in lines
        ]
    except Exception as exc:
        # Don't fail the whole request if the OCR engine can't load (e.g. no
        # internet for first-time model download) -- degrade gracefully and
        # flag it so the caller knows extraction didn't run.
        response.uncertainFields.append(f"OCR engine unavailable: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return response