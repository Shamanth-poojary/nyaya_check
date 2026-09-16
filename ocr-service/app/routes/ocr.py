import logging
from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.classification.merge import merge_extraction_results
from app.config import settings
from app.pipeline import process_single_image
from app.schemas.response import ExtractionResponse

router = APIRouter(tags=["Extraction"])
logger = logging.getLogger(__name__)

# Kept for backward compatibility with existing imports
MAX_IMAGES_PER_REQUEST = settings.max_images_per_request


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="Extract fields from a single product image",
)
async def extract(
    image: UploadFile = File(..., description="Product packaging photo to analyze"),
    preprocess_enabled: bool = Query(
        default=settings.preprocess_enabled_default,
        description="Enable OpenCV CLAHE contrast preprocessing. Defaults to false.",
    ),
) -> ExtractionResponse:
    """
    Single-image extraction. See `/extract/multi` for multi-photo extraction
    (the primary intended use case).

    Runs the full OCR pipeline:
      - Validates format and size against configured settings
      - Downscales to OCR target dimension (default 1600px max)
      - Executes PaddleOCR text line detection and recognition
      - Stitches horizontally fragmented adjacent text boxes
      - Classifies legal metrology fields (MRP, Net Qty, Dates, Manufacturer)
      - Measures relative font sizes, contrast buckets, and clearance
    """
    filename = image.filename or "unnamed"
    logger.info("POST /extract received 1 image: %s", filename)
    return await process_single_image(image, preprocess_enabled)


@router.post(
    "/extract/multi",
    response_model=ExtractionResponse,
    summary="Extract and merge fields across multiple product photos",
)
async def extract_multi(
    images: List[UploadFile] = File(..., description="List of product packaging photos (up to max_images_per_request)"),
    preprocess_enabled: bool = Query(
        default=settings.preprocess_enabled_default,
        description="Enable OpenCV CLAHE contrast preprocessing. Defaults to false.",
    ),
) -> ExtractionResponse:
    """
    Multi-image extraction -- the primary intended use case for this service.

    A single product photo rarely captures all mandatory declarations. This
    endpoint processes each uploaded photo independently and merges evidence:
      - Takes the highest-confidence extraction per structured field
      - Disagreements between photos on critical values (e.g. conflicting MRPs) are recorded in `uncertainFields`
      - Concatenates raw OCR lines and visual metrics
      - Tags every evidence element with `sourceImage`
    """
    count = len(images)
    max_allowed = settings.max_images_per_request
    if count > max_allowed:
        logger.warning("Rejected /extract/multi with %d images (> max %d)", count, max_allowed)
        raise HTTPException(
            status_code=400,
            detail=f"Too many images ({count}); max {max_allowed} per request.",
        )

    filenames = [img.filename or f"image_{i}" for i, img in enumerate(images)]
    logger.info("POST /extract/multi processing %d images: %s", count, ", ".join(filenames))

    results = [await process_single_image(img, preprocess_enabled) for img in images]
    return merge_extraction_results(results)
