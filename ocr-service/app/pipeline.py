"""
The core single-image extraction pipeline: validate -> preprocess (optional)
-> OCR -> normalize -> classify.

Pulled out of routes/ocr.py so both the single-image endpoint (/extract)
and the multi-image endpoint (/extract/multi) call the exact same logic
per photo -- multi-image extraction is just "run this once per photo, then
merge the results," not a separate implementation.
"""

import io
import os
import tempfile

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.classification.fields import classify_fields
from app.ocr.normalize import merge_split_lines
from app.ocr.paddle import run_ocr
from app.preprocessing.pipeline import PreprocessConfig, preprocess
from app.preprocessing.resize import resize_image
from app.schemas.response import BoundingBox, ExtractionResponse, RawOCRLine, empty_response
from app.visual.pipeline import run_visual_analysis

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 15

# Fields with `found`/`confidence` that get tagged with which photo they
# came from, once classify_fields has populated them.
STRUCTURED_FIELD_NAMES = [
    "commodity", "manufacturer", "packer", "importer", "mrp",
    "netQuantity", "manufacturingDate", "packingDate", "expiryDate", "batchNumber", "consumerCare",
]


async def process_single_image(image: UploadFile, preprocess_enabled: bool = False) -> ExtractionResponse:
    """Run the full pipeline on one uploaded image, tagging every piece of
    evidence with its source filename so multi-image merging can trace it
    back later."""
    source_name = image.filename or "unknown"

    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type ({source_name}): {image.content_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    contents = await image.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large ({source_name}): {size_mb:.1f} MB > {MAX_FILE_SIZE_MB} MB limit",
        )

    try:
        pil_image = Image.open(io.BytesIO(contents))
        pil_image.verify()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")  # reopen: verify() closes it
        width, height = pil_image.size
    except Exception:
        raise HTTPException(status_code=400, detail=f"File is not a valid image: {source_name}")

    response = empty_response(image_id=source_name, width=width, height=height)

    bgr_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    if preprocess_enabled:
        result = preprocess(bgr_image, PreprocessConfig())
        ocr_image_bgr, scale = result.image, result.scale
    else:
        ocr_image_bgr, scale = resize_image(bgr_image, max_dimension=1600)

    suffix = os.path.splitext(source_name)[1] or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, ocr_image_bgr)

        lines = run_ocr(tmp_path)
        lines = merge_split_lines(lines)  # Phase 4: repair same-row split detections
        inverse_scale = 1.0 / scale
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
                sourceImage=source_name,
            )
            for line in lines
        ]

        classify_fields(response, response.rawOCR)
        _tag_source_image(response, source_name)
        # Phase 02: populate visual evidence from the original (un-resized) image.
        # bgr_image is already in memory from the PIL→numpy conversion above;
        # we pass it here and do NOT persist it to disk beyond this request.
        response.visual = run_visual_analysis(bgr_image, response)
    except HTTPException:
        raise
    except Exception as exc:
        response.uncertainFields.append(f"OCR engine unavailable ({source_name}): {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return response


def _tag_source_image(response: ExtractionResponse, source_name: str) -> None:
    """Stamp which photo produced each classified field, for traceability
    once results from multiple photos get merged together."""
    for field_name in STRUCTURED_FIELD_NAMES:
        field = getattr(response, field_name)
        if getattr(field, "found", False):
            field.sourceImage = source_name
    for item in response.dimensions:
        item.sourceImage = source_name
    for item in response.quantityQualifiers:
        item.sourceImage = source_name
    for item in response.misleadingQuantityTerms:
        item.sourceImage = source_name
