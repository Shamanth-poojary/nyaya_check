"""
app/visual/pipeline.py — Phase 02

Orchestrator for all visual analysis sub-modules.

Entry point: run_visual_analysis(bgr_image, response) -> VisualEvidence

Called from app/pipeline.py after classification and source tagging, before
the response is returned.  The original BGR image is passed in-memory for
the duration of this call only — it is NOT persisted to disk.

Per-photo vs per-merge strategy:
  Visual evidence is computed PER PHOTO (for the single-image pipeline).
  In the multi-image merge flow (routes/ocr.py), each contributing photo
  produces its own VisualEvidence.  The final merged response's visual field
  is the evidence from the photo identified as the likely PDP by the layout
  heuristic — see routes/ocr.py for how merging is handled.
  This approach is simpler and more honest: each photo's visual metrics
  reflect that photo's actual pixel data, not a confused mix of multiple
  photos.
"""

import logging
from typing import Optional

import numpy as np

from app.schemas.response import ExtractionResponse, VisualEvidence
from app.visual.contrast import compute_contrast, compute_readability
from app.visual.font_size import compute_font_sizes
from app.visual.layout import identify_principal_display_panel
from app.visual.spacing import compute_quantity_clearance

logger = logging.getLogger(__name__)


def run_visual_analysis(
    bgr_image: Optional[np.ndarray],
    response: ExtractionResponse,
) -> VisualEvidence:
    """Run all visual analysis sub-modules and return a populated VisualEvidence.

    Args:
        bgr_image:  The original full-resolution BGR numpy array (from cv2 /
                    PIL conversion in app/pipeline.py).  May be None if the
                    image could not be decoded (e.g. OCR-only path); in that
                    case contrast metrics are skipped gracefully.
        response:   The ExtractionResponse after classification + source tagging.
                    Mutated only via response.uncertainFields on error; visual
                    field is NOT mutated here — the caller replaces it.

    Returns:
        A fully populated VisualEvidence object.  On any unexpected error in a
        sub-module, that sub-module's contribution is left empty/None and the
        error is logged + appended to response.uncertainFields so downstream
        consumers know the data is incomplete.
    """
    image_height: int = response.document.height
    image_width: int = response.document.width

    # ------------------------------------------------------------------ #
    # 1. Relative font sizes
    # ------------------------------------------------------------------ #
    try:
        font_size_entries, nq_median_ratio = compute_font_sizes(response)
    except Exception as exc:
        logger.warning("visual/font_size: unexpected error: %s", exc, exc_info=True)
        response.uncertainFields.append(f"visual/font_size failed: {exc}")
        font_size_entries, nq_median_ratio = [], None

    # ------------------------------------------------------------------ #
    # 2. Contrast
    # ------------------------------------------------------------------ #
    contrast_entries = []
    if bgr_image is not None:
        try:
            contrast_entries = compute_contrast(bgr_image, response)
        except Exception as exc:
            logger.warning("visual/contrast: unexpected error: %s", exc, exc_info=True)
            response.uncertainFields.append(f"visual/contrast failed: {exc}")
    else:
        response.uncertainFields.append(
            "visual/contrast: no image available; contrast metrics skipped."
        )

    # ------------------------------------------------------------------ #
    # 3. Readability
    # ------------------------------------------------------------------ #
    try:
        readability_entries = compute_readability(contrast_entries, font_size_entries)
    except Exception as exc:
        logger.warning("visual/readability: unexpected error: %s", exc, exc_info=True)
        response.uncertainFields.append(f"visual/readability failed: {exc}")
        readability_entries = []

    # ------------------------------------------------------------------ #
    # 4. Quantity clearance
    # ------------------------------------------------------------------ #
    try:
        qty_clearance = compute_quantity_clearance(response, image_width, image_height)
    except Exception as exc:
        logger.warning("visual/spacing: unexpected error: %s", exc, exc_info=True)
        response.uncertainFields.append(f"visual/spacing failed: {exc}")
        qty_clearance = None

    # ------------------------------------------------------------------ #
    # 5. Principal display panel
    # ------------------------------------------------------------------ #
    try:
        pdp = identify_principal_display_panel(response)
    except Exception as exc:
        logger.warning("visual/layout: unexpected error: %s", exc, exc_info=True)
        response.uncertainFields.append(f"visual/layout failed: {exc}")
        pdp = None

    return VisualEvidence(
        relativeFontSizes=font_size_entries,
        netQuantityMedianRatio=nq_median_ratio,
        contrast=contrast_entries,
        readability=readability_entries,
        quantityClearance=qty_clearance,
        principalDisplayPanel=pdp,
    )
