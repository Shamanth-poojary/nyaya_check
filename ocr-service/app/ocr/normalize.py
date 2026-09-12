"""
Phase 4: OCR normalization -- merge same-row split detections.

PaddleOCR sometimes splits a single physical text line (e.g. "MRP :RS 40")
into two separate detections ("MRP" and ":RS 40") when there's a visible
gap between a label and its value. Observed to happen MORE under CLAHE
contrast enhancement (Phase 3) -- increased local contrast makes the gap
more visually distinct -- but nothing here assumes preprocessing is the
only cause; PaddleOCR's line segmentation can be flaky either way.

Downstream classification assumes a label and its value live in the SAME
line. This step repairs that assumption by clustering detections into rows
(by vertical center, NOT just top-edge y -- label and value fonts often
have slightly different heights, so their bboxes don't share a ymin even
when visually on the same line) and merging horizontally-adjacent
detections within each row into one line, before classification ever sees
the data.
"""

from typing import List

from app.ocr.paddle import OCRLine

ROW_CENTER_TOLERANCE = 18   # pixels; max vertical-center difference to be considered the same row
MAX_HORIZONTAL_GAP = 40     # pixels; max gap between boxes to merge them within a row
MIN_HORIZONTAL_GAP = -20    # pixels; allow slight bbox overlap (detector imprecision)


def _center_y(line: OCRLine) -> float:
    return (line.bbox[1] + line.bbox[3]) / 2


def _cluster_into_rows(lines: List[OCRLine]) -> List[List[OCRLine]]:
    """Group lines into rows by vertical-center proximity, top to bottom."""
    ordered = sorted(lines, key=_center_y)
    rows: List[List[OCRLine]] = []
    row_centers: List[float] = []

    for line in ordered:
        center = _center_y(line)
        if rows and abs(center - row_centers[-1]) <= ROW_CENTER_TOLERANCE:
            rows[-1].append(line)
            row_centers[-1] = sum(_center_y(l) for l in rows[-1]) / len(rows[-1])  # running average
        else:
            rows.append([line])
            row_centers.append(center)

    return rows


def _merge_row(row: List[OCRLine]) -> List[OCRLine]:
    """Within one row, merge horizontally-adjacent boxes; keep genuinely
    separate columns (large horizontal gap) as distinct lines."""
    row_sorted = sorted(row, key=lambda l: l.bbox[0])
    merged: List[OCRLine] = []
    current = row_sorted[0]

    for nxt in row_sorted[1:]:
        gap = nxt.bbox[0] - current.bbox[2]
        if MIN_HORIZONTAL_GAP <= gap <= MAX_HORIZONTAL_GAP:
            merged_bbox = (
                min(current.bbox[0], nxt.bbox[0]),
                min(current.bbox[1], nxt.bbox[1]),
                max(current.bbox[2], nxt.bbox[2]),
                max(current.bbox[3], nxt.bbox[3]),
            )
            current = OCRLine(
                text=f"{current.text} {nxt.text}",
                bbox=merged_bbox,
                confidence=min(current.confidence, nxt.confidence),
            )
        else:
            merged.append(current)
            current = nxt
    merged.append(current)
    return merged


def merge_split_lines(lines: List[OCRLine]) -> List[OCRLine]:
    """Merge same-row, horizontally-adjacent OCR detections into one line.

    Order-independent: clusters by row first, so input order doesn't matter,
    and label/value font-height differences don't break row grouping.
    """
    if not lines:
        return lines

    rows = _cluster_into_rows(lines)
    merged: List[OCRLine] = []
    for row in rows:
        merged.extend(_merge_row(row))
    return merged
