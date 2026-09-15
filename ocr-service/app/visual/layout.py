"""
app/visual/layout.py — Phase 02

Principal Display Panel (PDP) heuristic.

Identifies which submitted photo is most likely the Principal Display Panel —
the panel that should carry the commodity identity, net quantity, and MRP
together per Legal Metrology (PCR) Rules 2011.

Heuristic: the sourceImage that contributed the most of {commodity,
netQuantity, mrp} (by count of PDP-relevant fields sourced from it, using the
existing `sourceImage` tags already stamped on every field by pipeline.py's
`_tag_source_image`).

IMPORTANT: This is a HEURISTIC INFERENCE, not a determination from photo
metadata (there is none in an uploaded photo).  The output always sets
isHeuristic=True and includes a note explaining the basis of the inference.
Single-image submissions are trivially identified as their own PDP.
"""

from collections import Counter
from typing import Optional

from app.schemas.response import ExtractionResponse, PrincipalDisplayPanel

# The three fields that together define the Principal Display Panel under
# Legal Metrology PCR 2011 Rules.  Using their response attribute names.
_PDP_FIELDS = ["commodity", "netQuantity", "mrp"]


def identify_principal_display_panel(
    response: ExtractionResponse,
) -> Optional[PrincipalDisplayPanel]:
    """Heuristically identify which source image is the Principal Display Panel.

    Args:
        response:  ExtractionResponse after classification and source tagging.

    Returns:
        PrincipalDisplayPanel describing the likely PDP image, or None if
        no sourceImage tags are present on any PDP-relevant field.
    """
    # Collect sourceImage values for each of the three PDP-defining fields.
    source_counts: Counter = Counter()
    field_sources = {}

    for attr_name in _PDP_FIELDS:
        field_obj = getattr(response, attr_name, None)
        if field_obj is None:
            continue
        src = getattr(field_obj, "sourceImage", None)
        if src:
            source_counts[src] += 1
            field_sources[attr_name] = src

    if not source_counts:
        # No PDP-relevant field has a sourceImage tag — cannot determine PDP.
        return PrincipalDisplayPanel(
            likelySourceImage=None,
            isHeuristic=True,
            note=(
                "Cannot determine PDP: none of commodity/netQuantity/mrp "
                "were successfully classified with a sourceImage tag."
            ),
        )

    # Find all source images and determine if this is a single-image submission.
    all_sources = set(source_counts.keys())

    if len(all_sources) == 1:
        # Single-image or all PDP fields from the same image.
        only_source = next(iter(all_sources))
        count = source_counts[only_source]

        # Distinguish a genuinely single-image submission from a multi-image
        # submission where all three PDP fields happen to come from one image.
        # Use sourceDocuments if available; fall back to rawOCR sourceImage set.
        all_rawocr_sources = {
            line.sourceImage for line in response.rawOCR if line.sourceImage
        }
        doc_sources = (
            {d.imageId for d in response.sourceDocuments}
            if response.sourceDocuments
            else set()
        )
        known_sources = doc_sources or all_rawocr_sources

        if len(known_sources) <= 1:
            note = (
                f"Single-image submission: '{only_source}' is trivially the PDP "
                f"since there is nothing to compare against. "
                f"PDP-relevant fields sourced from it: {count}/3."
            )
        else:
            note = (
                f"Multi-image submission ({len(known_sources)} images): "
                f"'{only_source}' sourced {count}/3 PDP-relevant fields "
                f"(commodity, netQuantity, mrp) — all three from the same image."
            )

        return PrincipalDisplayPanel(
            likelySourceImage=only_source,
            isHeuristic=True,
            note=note,
        )

    # Multi-image: pick the source with the most PDP fields.
    best_source, best_count = source_counts.most_common(1)[0]
    total_images = len(all_sources)

    note = (
        f"Multi-image submission ({total_images} images): "
        f"'{best_source}' sourced {best_count}/3 PDP-relevant fields "
        f"(commodity, netQuantity, mrp) — more than any other image. "
        f"Field-source breakdown: "
        + ", ".join(f"{k}←{v}" for k, v in field_sources.items())
        + ". Heuristic inference only."
    )

    return PrincipalDisplayPanel(
        likelySourceImage=best_source,
        isHeuristic=True,
        note=note,
    )
