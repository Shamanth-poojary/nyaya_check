"""
Merge N single-image ExtractionResponse objects (one per uploaded photo)
into ONE consolidated ExtractionResponse -- the actual point of multi-photo
extraction: a real product's mandatory declarations are rarely all visible
in a single photo (front panel has MRP/net qty, back panel has manufacturer/
consumer care, etc.), so the merged result is what a rules engine should
actually evaluate against, not any single photo's partial view.

Strategy:
  - Scalar/structured fields (mrp, manufacturer, dates, ...): take the
    highest-confidence `found=True` instance across all photos.
  - List fields (rawOCR, dimensions, quantityQualifiers, ...): concatenate,
    since each photo may show genuinely different qualifying phrases.
  - Conflicts (e.g. two photos disagreeing on MRP) are flagged in
    uncertainFields rather than silently resolved -- a rules engine
    shouldn't be handed a confident-looking number that's actually disputed
    evidence.
"""

from typing import List

from app.schemas.response import DocumentMeta, ExtractionResponse, empty_response

STRUCTURED_FIELD_NAMES = [
    "commodity", "manufacturer", "packer", "importer", "mrp",
    "netQuantity", "manufacturingDate", "expiryDate", "batchNumber", "consumerCare",
]

# For each structured field, which attribute(s) identify "the same value" --
# used to detect disagreement between photos, not just pick a winner.
CONFLICT_KEYS = {
    "mrp": ["value"],
    "batchNumber": ["value"],
    "manufacturingDate": ["day", "month", "year"],
    "expiryDate": ["day", "month", "year"],
    "netQuantity": ["normalizedValue", "normalizedUnit"],
    "commodity": ["category"],
}


def merge_extraction_results(results: List[ExtractionResponse]) -> ExtractionResponse:
    if not results:
        raise ValueError("merge_extraction_results requires at least one result")
    if len(results) == 1:
        single = results[0]
        single.sourceDocuments = [single.document]
        return single

    merged = empty_response(image_id="multi-image", width=0, height=0)
    merged.sourceDocuments = [r.document for r in results]
    merged.document = results[0].document  # representative; sourceDocuments has the full list

    for field_name in STRUCTURED_FIELD_NAMES:
        candidates = [getattr(r, field_name) for r in results]
        setattr(merged, field_name, _pick_best(candidates))
        _flag_conflicts(merged, field_name, candidates)

    merged.dimensions = [d for r in results for d in r.dimensions]
    merged.quantityQualifiers = [q for r in results for q in r.quantityQualifiers]
    merged.misleadingQuantityTerms = [m for r in results for m in r.misleadingQuantityTerms]
    merged.rawOCR = [l for r in results for l in r.rawOCR]
    merged.uncertainFields = [u for r in results for u in r.uncertainFields] + merged.uncertainFields

    return merged


def _pick_best(candidates: list):
    """Return the highest-confidence `found=True` candidate, or the first
    (not-found) candidate if none were found in any photo."""
    found = [c for c in candidates if getattr(c, "found", False)]
    if not found:
        return candidates[0]
    return max(found, key=lambda c: c.confidence)


def _flag_conflicts(merged: ExtractionResponse, field_name: str, candidates: list) -> None:
    """If 2+ photos found this field with genuinely different values,
    flag it -- silently picking the highest-confidence one could hide a
    real problem (e.g. two different products' labels got mixed into one
    upload by mistake)."""
    keys = CONFLICT_KEYS.get(field_name)
    if not keys:
        return

    found = [c for c in candidates if getattr(c, "found", False)]
    if len(found) < 2:
        return

    distinct_values = {tuple(getattr(c, k) for k in keys) for c in found}
    if len(distinct_values) > 1:
        sources = [f"{getattr(c, 'sourceImage', '?')}: {tuple(getattr(c, k) for k in keys)}" for c in found]
        merged.uncertainFields.append(
            f"Conflicting '{field_name}' values across photos ({'; '.join(sources)}); "
            "used the highest-confidence one -- verify manually."
        )
