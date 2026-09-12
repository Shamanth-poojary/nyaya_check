import io
import os
import tempfile

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.classification.fields import classify_fields
from app.ocr.paddle import run_ocr
from app.preprocessing.pipeline import PreprocessConfig, preprocess
from app.schemas.response import BoundingBox, ExtractionResponse, RawOCRLine, empty_response

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 15


@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    image: UploadFile = File(...),
    preprocess_enabled: bool = True,
) -> ExtractionResponse:
    """
    Validate the upload, optionally run it through the OpenCV preprocessing
    pipeline (Phase 3), then through PaddleOCR (Phase 2), populating rawOCR.

    Set `preprocess_enabled=false` (query param) to run OCR on the raw
    image untouched -- use this to A/B test whether preprocessing is
    actually helping on your own test images, per the project plan's
    "measure, don't assume" guidance.

    Later phases still to come:
      Phase 4 - OCR normalization
      Phase 5/6/7 - Regex + keyword + NER classification, commodity category
      Phase 8 - Visual analysis
      Phase 9 - Evidence assembly
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
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")  # reopen: verify() closes it
        width, height = pil_image.size
    except Exception:
        raise HTTPException(status_code=400, detail="File is not a valid image")

    response = empty_response(image_id=image.filename or "unknown", width=width, height=height)

    # PIL gives RGB; OpenCV expects BGR.
    bgr_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    if preprocess_enabled:
        result = preprocess(bgr_image, PreprocessConfig())
        ocr_image_bgr = result.image
        scale = result.scale
    else:
        # Still resize even with preprocessing off, purely for OCR speed --
        # this is NOT part of the accuracy comparison, just keeps the
        # "off" path from being unusably slow on large phone photos.
        from app.preprocessing.resize import resize_image

        ocr_image_bgr, scale = resize_image(bgr_image, max_dimension=1600)

    suffix = os.path.splitext(image.filename or "")[1] or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, ocr_image_bgr)

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

        # Phase 5: classify raw OCR lines into named fields. rawOCR above
        # stays untouched as the raw evidence layer -- this only adds
        # structure on top of it.
        classify_fields(response, response.rawOCR)
    except Exception as exc:
        # Don't fail the whole request if the OCR engine can't load (e.g. no
        # internet for first-time model download) -- degrade gracefully and
        # flag it so the caller knows extraction didn't run.
        response.uncertainFields.append(f"OCR engine unavailable: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return response
