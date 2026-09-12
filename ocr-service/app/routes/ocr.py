from typing import List

from fastapi import APIRouter, File, UploadFile

from app.classification.merge import merge_extraction_results
from app.pipeline import process_single_image
from app.schemas.response import ExtractionResponse

router = APIRouter()

MAX_IMAGES_PER_REQUEST = 10


@router.post("/extract", response_model=ExtractionResponse)
async def extract(
    image: UploadFile = File(...),
    preprocess_enabled: bool = False,
) -> ExtractionResponse:
    """
    Single-image extraction. See /extract/multi for multi-photo extraction
    (the primary intended use case -- see that endpoint's docstring).

    Defaults to `preprocess_enabled=False`: A/B testing on real photos
    showed CLAHE contrast enhancement (Phase 3) can cause PaddleOCR to
    split a single physical line into two separate detections. Line-merging
    normalization (Phase 4) now repairs this either way, but raw OCR
    remains the safer default until preprocessing shows a clear, proven
    benefit on a broader test set.
    """
    return await process_single_image(image, preprocess_enabled)


@router.post("/extract/multi", response_model=ExtractionResponse)
async def extract_multi(
    images: List[UploadFile] = File(...),
    preprocess_enabled: bool = False,
) -> ExtractionResponse:
    """
    Multi-image extraction -- the primary intended use case for this
    service. A single product photo rarely shows every mandatory
    declaration (front panel has MRP/net qty, back panel has manufacturer/
    consumer care, a side panel might show dimensions or "when packed"
    wording); this endpoint runs the SAME single-image pipeline on each
    uploaded photo independently, then merges the results into one
    consolidated ExtractionResponse.

    Merge behavior:
      - Each structured field (mrp, manufacturer, dates, ...) takes the
        highest-confidence match found across all photos.
      - rawOCR, dimensions, and qualifier/misleading-term lists are
        concatenated across all photos (nothing is discarded).
      - Every piece of evidence is tagged with `sourceImage` (the filename
        it came from), and `sourceDocuments` lists every photo submitted.
      - If two photos disagree on a fact that should be consistent (e.g.
        different MRP values), it's flagged in `uncertainFields` rather
        than silently resolved -- that kind of conflict is worth a human
        look, not a silent pick.

    Response shape is IDENTICAL to /extract's single-image response --
    downstream consumers (rules engine) don't need to know or care how
    many photos went in.
    """
    if len(images) > MAX_IMAGES_PER_REQUEST:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Too many images ({len(images)}); max {MAX_IMAGES_PER_REQUEST} per request.",
        )

    results = [await process_single_image(img, preprocess_enabled) for img in images]
    return merge_extraction_results(results)
