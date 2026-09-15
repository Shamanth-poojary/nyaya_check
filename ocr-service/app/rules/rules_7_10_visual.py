"""
app/rules/rules_7_10_visual.py — Rules 7–10 visual/spatial checks.

Legal Metrology (Packaged Commodities) Rules, 2011:
  Rule 7  — Manner of declaration (legibility requirements)
  Rule 8  — Height of numerals in net quantity declaration
  Rule 9  — Manner of expressing net quantity
  Rule 10 — Adequate space/clearance around net quantity declaration

ALL results from this module are WARNING or NEEDS_REVIEW, never BLOCKING.
Rationale (documented in 03_rules_engine.md and phase 02 visual module):
  Visual analysis is a heuristic approximation derived from uncalibrated
  pixel data — a compliance tool must not claim certainty it doesn't have
  about physical font heights or clearances measured from a photo.

TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15

ARCHITECTURAL RULE: this module imports ONLY from:
  - app.schemas.response   (ExtractionResponse and field models)
  - app.schemas.compliance (RuleResult, Severity)
  NO imports from app.ocr, app.preprocessing, or app.classification.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.compliance import RuleResult, Severity
from app.schemas.response import ExtractionResponse

# ---------------------------------------------------------------------------
# Thresholds (documented here, not magic numbers)
# ---------------------------------------------------------------------------

# Minimum ratio of a field's bbox height to the net quantity bbox height
# below which we flag potential numeral-size non-compliance (Rules 7–8).
# Rule 8 specifies minimum numeral heights in mm; since we only have pixel
# ratios from an uncalibrated photo, we use a conservative relative heuristic.
# A ratio < 0.5 means the field text is less than half the height of the
# net-quantity numeral, which is unlikely to meet the physical size requirements.
# This is a WARNING, not BLOCKING — it is a heuristic signal only.
# TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
MIN_FONT_RATIO_THRESHOLD: float = 0.5

# Minimum clearance ratio (gap / net_quantity height) around the net quantity
# field below which we warn about potential crowding (Rule 10).
# A ratio < 0.5 means the nearest neighbour is closer than half the numeral
# height — indicative of insufficient clearance, but not a certified measurement.
# TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
MIN_CLEARANCE_RATIO_THRESHOLD: float = 0.5


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _make_result(
    rule_id: str,
    reference: str,
    description: str,
    passed: bool,
    severity: Severity,
    evidence_field: Optional[str],
    evidence_value: Optional[str],
    evidence_confidence: Optional[float],
    source_image: Optional[str],
    message: str,
) -> RuleResult:
    return RuleResult(
        ruleId=rule_id,
        ruleReference=reference,
        description=description,
        passed=passed,
        severity=severity,
        evidenceField=evidence_field,
        evidenceValue=evidence_value,
        evidenceConfidence=evidence_confidence,
        sourceImage=source_image,
        message=message,
    )


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_font_size_ratios(response: ExtractionResponse) -> List[RuleResult]:
    """Rules 7–8: Check that important declared fields are not rendered
    at an unusually small relative font size compared to the net quantity numeral.

    Emits one RuleResult per field inspected.
    All results are WARNING (if below threshold) or INFO (passing).

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rules 7–8 "
        "(legibility and numeral height requirements — heuristic pixel ratio)"
    )
    results: List[RuleResult] = []

    if not response.visual.relativeFontSizes:
        # No visual data available — emit a single NEEDS_REVIEW
        results.append(_make_result(
            rule_id="rule_7_8_font_size_no_data",
            reference=reference,
            description="Font-size ratios not available (no visual analysis data)",
            passed=True,
            severity=Severity.NEEDS_REVIEW,
            evidence_field="visual.relativeFontSizes",
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message="No font-size data from visual analysis. Cannot evaluate Rules 7–8.",
        ))
        return results

    for entry in response.visual.relativeFontSizes:
        field = entry.field
        ratio = entry.ratioToNetQuantity

        if ratio is None:
            # Can't compute ratio (netQuantity has no bbox) — NEEDS_REVIEW
            results.append(_make_result(
                rule_id=f"rule_7_8_font_size_{field}",
                reference=reference,
                description=f"Font-size ratio for '{field}' relative to net quantity",
                passed=True,
                severity=Severity.NEEDS_REVIEW,
                evidence_field=f"visual.relativeFontSizes[{field}]",
                evidence_value=f"heightPx={entry.heightPx}",
                evidence_confidence=None,
                source_image=None,
                message=(
                    f"Cannot compute font-size ratio for '{field}' — "
                    "net quantity has no bounding box."
                ),
            ))
            continue

        if ratio < MIN_FONT_RATIO_THRESHOLD:
            results.append(_make_result(
                rule_id=f"rule_7_8_font_size_{field}",
                reference=reference,
                description=f"Font-size ratio for '{field}' relative to net quantity numeral",
                passed=False,
                severity=Severity.WARNING,
                evidence_field=f"visual.relativeFontSizes[{field}]",
                evidence_value=f"ratio={ratio:.3f} (threshold={MIN_FONT_RATIO_THRESHOLD})",
                evidence_confidence=None,
                source_image=None,
                message=(
                    f"Field '{field}' appears smaller than {MIN_FONT_RATIO_THRESHOLD:.0%} "
                    f"of net quantity height (ratio={ratio:.3f}). "
                    "Potential legibility issue — heuristic signal only, verify physically."
                ),
            ))
        else:
            results.append(_make_result(
                rule_id=f"rule_7_8_font_size_{field}",
                reference=reference,
                description=f"Font-size ratio for '{field}' relative to net quantity numeral",
                passed=True,
                severity=Severity.INFO,
                evidence_field=f"visual.relativeFontSizes[{field}]",
                evidence_value=f"ratio={ratio:.3f}",
                evidence_confidence=None,
                source_image=None,
                message=f"Field '{field}' font-size ratio {ratio:.3f} ≥ threshold {MIN_FONT_RATIO_THRESHOLD}.",
            ))

    return results


def check_readability(response: ExtractionResponse) -> List[RuleResult]:
    """Rule 7: Declarations must be clearly and legibly printed.

    Checks the qualitative readability classification from phase 02.
    "hard_to_read" fields are flagged as WARNING — this is a heuristic signal.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 7 "
        "(legibility — heuristic contrast/size signal from visual analysis)"
    )
    results: List[RuleResult] = []

    if not response.visual.readability:
        results.append(_make_result(
            rule_id="rule_7_readability_no_data",
            reference=reference,
            description="Readability assessment not available",
            passed=True,
            severity=Severity.NEEDS_REVIEW,
            evidence_field="visual.readability",
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message="No readability data from visual analysis. Cannot evaluate Rule 7.",
        ))
        return results

    for entry in response.visual.readability:
        field = entry.field
        if entry.readability == "hard_to_read":
            results.append(_make_result(
                rule_id=f"rule_7_readability_{field}",
                reference=reference,
                description=f"Readability of field '{field}'",
                passed=False,
                severity=Severity.WARNING,
                evidence_field=f"visual.readability[{field}]",
                evidence_value=f"readability={entry.readability}, reason={entry.reason}",
                evidence_confidence=None,
                source_image=None,
                message=(
                    f"Field '{field}' flagged as hard-to-read "
                    f"(reason: {entry.reason}). "
                    "Heuristic signal — verify legibility physically."
                ),
            ))
        else:
            results.append(_make_result(
                rule_id=f"rule_7_readability_{field}",
                reference=reference,
                description=f"Readability of field '{field}'",
                passed=True,
                severity=Severity.INFO,
                evidence_field=f"visual.readability[{field}]",
                evidence_value=f"readability={entry.readability}",
                evidence_confidence=None,
                source_image=None,
                message=f"Field '{field}' assessed as readable (reason: {entry.reason}).",
            ))

    return results


def check_quantity_clearance(response: ExtractionResponse) -> List[RuleResult]:
    """Rule 10: Adequate space/clearance around the net quantity declaration.

    The pixel-ratio clearance measured by phase 02 is compared against a
    heuristic threshold. Results are WARNING or NEEDS_REVIEW, never BLOCKING.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 10 "
        "(space around net quantity — heuristic pixel-ratio from visual analysis)"
    )
    results: List[RuleResult] = []

    qc = response.visual.quantityClearance
    if qc is None:
        results.append(_make_result(
            rule_id="rule_10_quantity_clearance_no_data",
            reference=reference,
            description="Whitespace clearance around net quantity declaration",
            passed=True,
            severity=Severity.NEEDS_REVIEW,
            evidence_field="visual.quantityClearance",
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message=(
                "Quantity clearance data unavailable — "
                "net quantity field may have no bounding box. Cannot evaluate Rule 10."
            ),
        ))
        return results

    directions = {
        "above": qc.aboveRatio,
        "below": qc.belowRatio,
        "left": qc.leftRatio,
        "right": qc.rightRatio,
    }

    for direction, ratio in directions.items():
        rule_id = f"rule_10_quantity_clearance_{direction}"
        description = f"Clearance {direction} net quantity declaration"
        if ratio is None:
            results.append(_make_result(
                rule_id=rule_id,
                reference=reference,
                description=description,
                passed=True,
                severity=Severity.NEEDS_REVIEW,
                evidence_field=f"visual.quantityClearance.{direction}Ratio",
                evidence_value="None",
                evidence_confidence=None,
                source_image=None,
                message=f"Clearance {direction} not measurable from available bounding box data.",
            ))
        elif ratio < MIN_CLEARANCE_RATIO_THRESHOLD:
            results.append(_make_result(
                rule_id=rule_id,
                reference=reference,
                description=description,
                passed=False,
                severity=Severity.WARNING,
                evidence_field=f"visual.quantityClearance.{direction}Ratio",
                evidence_value=f"ratio={ratio:.3f} (threshold={MIN_CLEARANCE_RATIO_THRESHOLD})",
                evidence_confidence=None,
                source_image=None,
                message=(
                    f"Net quantity clearance {direction} ({ratio:.3f}) is below threshold "
                    f"({MIN_CLEARANCE_RATIO_THRESHOLD}). "
                    "Potential crowding — heuristic signal only. Note: "
                    + (qc.note or "")
                ),

            ))
        else:
            results.append(_make_result(
                rule_id=rule_id,
                reference=reference,
                description=description,
                passed=True,
                severity=Severity.INFO,
                evidence_field=f"visual.quantityClearance.{direction}Ratio",
                evidence_value=f"ratio={ratio:.3f}",
                evidence_confidence=None,
                source_image=None,
                message=f"Net quantity clearance {direction} ({ratio:.3f}) meets threshold.",
            ))

    return results


# ---------------------------------------------------------------------------
# Public: run all Rules 7–10 checks
# ---------------------------------------------------------------------------

def evaluate_rules_7_10(response: ExtractionResponse) -> List[RuleResult]:
    """Run all Rules 7–10 visual checks and return a flat list of RuleResults."""
    results: List[RuleResult] = []
    results.extend(check_font_size_ratios(response))
    results.extend(check_readability(response))
    results.extend(check_quantity_clearance(response))
    return results
