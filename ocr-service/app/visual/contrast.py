"""
app/visual/contrast.py — Phase 02

Bbox-region contrast measurement and readability scoring.

Contrast metric: standard deviation of grayscale pixel intensity within the
cropped bbox region.  This is a RELATIVE indicator of local contrast — not a
photometrically calibrated measurement and not comparable across photos taken
under different lighting conditions.

Thresholds (empirically chosen):
  std < 20  → "low"    Nearly uniform region: heavy glare, washed-out print,
                       or very light text on a similarly-tinted background.
  20 ≤ std < 50 → "medium"  Moderate contrast: colored text on colored bg,
                             slightly busy backgrounds, faint shadows.
  std ≥ 50  → "high"   Clear contrast: dark text on light background (or
                        vice versa) — typical of well-printed black-on-white
                        compliance text.

Readability combination heuristic:
  hard_to_read  if  bucket == "low"
                OR  (bucket == "medium" AND ratioToNetQuantity < 0.5)
  readable      otherwise

This heuristic is intentionally simple and is documented here so the Phase 03
rules engine knows exactly what it means when it receives this signal.
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.schemas.response import (
    BoundingBox,
    ContrastEntry,
    ExtractionResponse,
    FontSizeEntry,
    ReadabilityEntry,
)

# Contrast bucket thresholds.
# These were selected by inspecting synthetic images (solid backgrounds,
# cv2.putText regions) and cross-referencing with the expected behavior on
# real label photos:
#   - A pure white 100×40 crop gives std ≈ 0–5
#   - Light-gray text on white gives std ≈ 10–18
#   - Black text on white gives std ≈ 55–90
#   - Colored text on colored backgrounds typically sits at 25–45
CONTRAST_LOW_THRESHOLD = 20.0    # below this → "low"
CONTRAST_HIGH_THRESHOLD = 50.0   # at or above this → "high"

# The ratio threshold below which a medium-contrast field is considered
# hard to read due to its small size relative to the net quantity line.
SMALL_SIZE_RATIO_THRESHOLD = 0.5


def _bucket(std_dev: float) -> str:
    """Map a grayscale std-dev to a qualitative contrast bucket."""
    if std_dev < CONTRAST_LOW_THRESHOLD:
        return "low"
    if std_dev < CONTRAST_HIGH_THRESHOLD:
        return "medium"
    return "high"


def _crop_and_measure(bgr_image: np.ndarray, bbox: BoundingBox) -> Optional[float]:
    """Crop the bbox region from the image and return grayscale std-dev.

    Returns None if the crop is empty or degenerate (shouldn't happen in
    production but guards against bad OCR bboxes).
    """
    h_img, w_img = bgr_image.shape[:2]

    # Clamp bbox coordinates to image boundaries.
    x1 = max(0, min(bbox.xmin, w_img - 1))
    y1 = max(0, min(bbox.ymin, h_img - 1))
    x2 = max(x1 + 1, min(bbox.xmax, w_img))
    y2 = max(y1 + 1, min(bbox.ymax, h_img))

    crop_bgr = bgr_image[y1:y2, x1:x2]
    if crop_bgr.size == 0:
        return None

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    return float(np.std(gray))


# Fields and their response attributes — mirrors font_size.py
_BBOX_FIELDS: List[Tuple[str, str]] = [
    ("mrp",               "mrp"),
    ("netQuantity",       "netQuantity"),
    ("manufacturingDate", "manufacturingDate"),
    ("packingDate",       "packingDate"),
    ("expiryDate",        "expiryDate"),
    ("batchNumber",       "batchNumber"),
    ("consumerCare",      "consumerCare"),
]


def compute_contrast(
    bgr_image: np.ndarray,
    response: ExtractionResponse,
) -> List[ContrastEntry]:
    """Measure contrast for every classified field that has a bbox.

    Args:
        bgr_image:  The original full-resolution BGR image as a numpy array.
                    It must remain in memory only for the duration of this call.
        response:   The ExtractionResponse after classification.

    Returns:
        List[ContrastEntry] — one entry per field with a measurable bbox.
    """
    entries: List[ContrastEntry] = []

    for attr_name, label in _BBOX_FIELDS:
        field_obj = getattr(response, attr_name, None)
        if field_obj is None:
            continue
        bbox = getattr(field_obj, "bbox", None)
        if bbox is None:
            continue

        std_dev = _crop_and_measure(bgr_image, bbox)
        if std_dev is None:
            continue

        entries.append(ContrastEntry(
            field=label,
            stdDev=round(std_dev, 3),
            bucket=_bucket(std_dev),
        ))

    return entries


def compute_readability(
    contrast_entries: List[ContrastEntry],
    font_size_entries: List[FontSizeEntry],
) -> List[ReadabilityEntry]:
    """Derive per-field readability flags from contrast and font-size data.

    Combination logic (heuristic — see module docstring):
      hard_to_read  if  bucket == "low"
                    OR  (bucket == "medium" AND ratioToNetQuantity < 0.5)
      readable      otherwise

    Fields with no contrast data are skipped (no image crop available).

    Args:
        contrast_entries:   Output of compute_contrast().
        font_size_entries:  Output of compute_font_sizes() from font_size.py.

    Returns:
        List[ReadabilityEntry] — one entry per field present in contrast_entries.
    """
    # Build a lookup from field name → ratio for quick access
    ratio_by_field = {e.field: e.ratioToNetQuantity for e in font_size_entries}

    entries: List[ReadabilityEntry] = []

    for ce in contrast_entries:
        ratio = ratio_by_field.get(ce.field)

        if ce.bucket == "low":
            readability = "hard_to_read"
            reason = "low_contrast"
        elif ce.bucket == "medium" and ratio is not None and ratio < SMALL_SIZE_RATIO_THRESHOLD:
            readability = "hard_to_read"
            reason = "small_relative_size"
        else:
            readability = "readable"
            reason = "ok"

        entries.append(ReadabilityEntry(
            field=ce.field,
            readability=readability,
            reason=reason,
        ))

    return entries
