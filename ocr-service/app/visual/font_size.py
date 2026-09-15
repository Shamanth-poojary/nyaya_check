"""
app/visual/font_size.py — Phase 02

Relative font-size ratio calculations.

Computes bbox-height ratios for all classified fields that have a bbox,
relative to the net quantity field's bbox height. Also computes the ratio
of the net quantity's height to the median height of all rawOCR lines on
the same photo, as a "is this declaration unusually small?" signal.

IMPORTANT: All values are RELATIVE pixel ratios within a single uncalibrated
photo.  No physical measurements (mm, point sizes) are produced or implied.
"""

from statistics import median
from typing import List, Optional, Tuple

from app.schemas.response import (
    BoundingBox,
    ExtractionResponse,
    FontSizeEntry,
)

# Ordered list of (response_attribute_name, output_field_label) pairs for
# every classified field that carries a bbox. This drives the generic loop
# so new fields can be added in one place.
_BBOX_FIELDS: List[Tuple[str, str]] = [
    ("mrp",               "mrp"),
    ("netQuantity",       "netQuantity"),
    ("manufacturingDate", "manufacturingDate"),
    ("packingDate",       "packingDate"),
    ("expiryDate",        "expiryDate"),
    ("batchNumber",       "batchNumber"),
    ("consumerCare",      "consumerCare"),
]


def _bbox_height(bbox: BoundingBox) -> int:
    """Return the pixel height of a bounding box."""
    return max(bbox.ymax - bbox.ymin, 1)  # guard against degenerate boxes


def compute_font_sizes(
    response: ExtractionResponse,
) -> Tuple[List[FontSizeEntry], Optional[float]]:
    """Compute relative font-size entries for all classified fields with bboxes.

    Returns:
        entries:               List[FontSizeEntry] — one entry per field with a bbox.
        net_quantity_median_ratio: Optional[float] — netQuantity height / median
                               rawOCR line height.  None if netQuantity has no
                               bbox or rawOCR is empty.
    """
    # Determine net quantity bbox height once — used as the denominator for ratios.
    nq_bbox = response.netQuantity.bbox
    nq_height: Optional[int] = _bbox_height(nq_bbox) if nq_bbox else None

    entries: List[FontSizeEntry] = []

    for attr_name, label in _BBOX_FIELDS:
        field_obj = getattr(response, attr_name, None)
        if field_obj is None:
            continue
        bbox = getattr(field_obj, "bbox", None)
        if bbox is None:
            continue

        h = _bbox_height(bbox)
        ratio: Optional[float] = None
        if nq_height is not None:
            ratio = round(h / nq_height, 4)

        entries.append(FontSizeEntry(
            field=label,
            heightPx=h,
            ratioToNetQuantity=ratio,
        ))

    # Also include dimensions (list field — pick the first bbox found)
    for dim in response.dimensions:
        if dim.bbox:
            h = _bbox_height(dim.bbox)
            ratio = round(h / nq_height, 4) if nq_height else None
            entries.append(FontSizeEntry(
                field="dimension",
                heightPx=h,
                ratioToNetQuantity=ratio,
            ))
            break  # one representative dimension entry is enough

    # Compute net quantity / median rawOCR ratio
    net_quantity_median_ratio: Optional[float] = None
    if nq_height is not None and response.rawOCR:
        line_heights = [
            _bbox_height(line.bbox)
            for line in response.rawOCR
            if line.bbox is not None
        ]
        if line_heights:
            med = median(line_heights)
            if med > 0:
                net_quantity_median_ratio = round(nq_height / med, 4)

    return entries, net_quantity_median_ratio
