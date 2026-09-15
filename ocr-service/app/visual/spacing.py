"""
app/visual/spacing.py — Phase 02

Quantity clearance measurement.

Rule 7 (Legal Metrology PCR 2011) requires minimum blank space around the
net quantity declaration.  This module measures the whitespace margin around
the net quantity bbox by finding, for each of the four cardinal directions,
the distance to the nearest other text bbox (from rawOCR) in that direction,
or to the image edge if no other text is closer.

All distances are expressed as RATIOS relative to the net quantity's own
bbox height — NOT in absolute pixels, mm, or any other physical unit.  This
is a deliberate design constraint: the photo is uncalibrated and no physical
measurement can be inferred from it.

Geometry convention:
  - Image origin (0, 0) is top-left.
  - ymin is the TOP edge of a bbox, ymax is the BOTTOM edge.
  - xmin is the LEFT edge, xmax is the RIGHT edge.
  - "above" = smaller y values; "below" = larger y values.

A bbox is considered a "neighbor in direction X" if it OVERLAPS horizontally
(for above/below) or vertically (for left/right) with the net quantity bbox —
bboxes that are in a completely different column/row are not counted as
clearance obstacles in that direction.
"""

from typing import List, Optional

from app.schemas.response import BoundingBox, ExtractionResponse, QuantityClearance, RawOCRLine

# Minimum overlap fraction required for a bbox to be counted as a neighbor
# in a given direction.  0.0 means any horizontal/vertical overlap counts;
# raising it reduces false positives from barely-touching bboxes in adjacent
# columns.
_OVERLAP_FRACTION = 0.0


def _horizontal_overlap(a: BoundingBox, b: BoundingBox) -> float:
    """Return the fraction of 'a' that horizontally overlaps with 'b'."""
    overlap = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    width_a = max(a.xmax - a.xmin, 1)
    return max(0.0, overlap / width_a)


def _vertical_overlap(a: BoundingBox, b: BoundingBox) -> float:
    """Return the fraction of 'a' that vertically overlaps with 'b'."""
    overlap = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    height_a = max(a.ymax - a.ymin, 1)
    return max(0.0, overlap / height_a)


def compute_quantity_clearance(
    response: ExtractionResponse,
    image_width: int,
    image_height: int,
) -> Optional[QuantityClearance]:
    """Measure the clearance (whitespace) around the net quantity bbox.

    Args:
        response:      ExtractionResponse after classification and visual analysis.
        image_width:   Width of the original photo in pixels.
        image_height:  Height of the original photo in pixels.

    Returns:
        QuantityClearance with ratios in each direction, or None if the
        netQuantity field has no bbox (clearance cannot be computed).
    """
    nq_bbox = response.netQuantity.bbox
    if nq_bbox is None:
        return None

    nq_height = max(nq_bbox.ymax - nq_bbox.ymin, 1)

    # Collect all OTHER rawOCR bboxes (exclude the net quantity bbox itself).
    other_bboxes: List[BoundingBox] = []
    for line in response.rawOCR:
        if line.bbox is None:
            continue
        # Skip the bbox that exactly matches the net quantity bbox (same object)
        if (
            line.bbox.xmin == nq_bbox.xmin
            and line.bbox.ymin == nq_bbox.ymin
            and line.bbox.xmax == nq_bbox.xmax
            and line.bbox.ymax == nq_bbox.ymax
        ):
            continue
        other_bboxes.append(line.bbox)

    # --- ABOVE: nearest text bottom edge that is above nq_bbox.ymin, with horizontal overlap ---
    above_dist: float = float(nq_bbox.ymin)  # default: distance to image top edge
    for b in other_bboxes:
        if b.ymax <= nq_bbox.ymin:  # b is entirely above nq
            if _horizontal_overlap(nq_bbox, b) > _OVERLAP_FRACTION:
                gap = nq_bbox.ymin - b.ymax
                if gap < above_dist:
                    above_dist = gap

    # --- BELOW: nearest text top edge that is below nq_bbox.ymax, with horizontal overlap ---
    below_dist: float = float(image_height - nq_bbox.ymax)  # default: distance to image bottom
    for b in other_bboxes:
        if b.ymin >= nq_bbox.ymax:  # b is entirely below nq
            if _horizontal_overlap(nq_bbox, b) > _OVERLAP_FRACTION:
                gap = b.ymin - nq_bbox.ymax
                if gap < below_dist:
                    below_dist = gap

    # --- LEFT: nearest text right edge that is left of nq_bbox.xmin, with vertical overlap ---
    left_dist: float = float(nq_bbox.xmin)  # default: distance to left image edge
    for b in other_bboxes:
        if b.xmax <= nq_bbox.xmin:  # b is entirely left of nq
            if _vertical_overlap(nq_bbox, b) > _OVERLAP_FRACTION:
                gap = nq_bbox.xmin - b.xmax
                if gap < left_dist:
                    left_dist = gap

    # --- RIGHT: nearest text left edge that is right of nq_bbox.xmax, with vertical overlap ---
    right_dist: float = float(image_width - nq_bbox.xmax)  # default: distance to right image edge
    for b in other_bboxes:
        if b.xmin >= nq_bbox.xmax:  # b is entirely right of nq
            if _vertical_overlap(nq_bbox, b) > _OVERLAP_FRACTION:
                gap = b.xmin - nq_bbox.xmax
                if gap < right_dist:
                    right_dist = gap

    # Express all distances as ratios to nq_height.
    return QuantityClearance(
        aboveRatio=round(above_dist / nq_height, 4),
        belowRatio=round(below_dist / nq_height, 4),
        leftRatio=round(left_dist / nq_height, 4),
        rightRatio=round(right_dist / nq_height, 4),
        note=(
            "Clearance expressed as ratio to netQuantity bbox height "
            f"({nq_height}px in original-photo coordinates). "
            "These are pixel ratios, not physical mm clearances."
        ),
    )
