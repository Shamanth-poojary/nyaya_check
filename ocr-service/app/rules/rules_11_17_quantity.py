"""
app/rules/rules_11_17_quantity.py — Rules 11–17 quantity, unit, and misleading-term checks.

Legal Metrology (Packaged Commodities) Rules, 2011:
  Rule 11 — Standard quantities for specified commodities (Second Schedule)
  Rule 12 — Method of expressing net quantity
  Rule 13 — Use of SI units
  Rule 14 — Prohibition of certain expressions (misleading terms)
  Rule 15 — Qualifiers on net quantity
  Rule 16 — Numerical accuracy
  Rule 17 — Quantity declared in dual units

TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15

ARCHITECTURAL RULE: this module imports ONLY from:
  - app.schemas.response   (ExtractionResponse and field models)
  - app.schemas.compliance (RuleResult, Severity, LOW_CONFIDENCE_THRESHOLD)
  - app.rules.schedules    (permitted_qualifier_types, is_unit_valid_for_type,
                            category_has_schedule_data)
  NO imports from app.ocr, app.preprocessing, or app.classification.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.compliance import LOW_CONFIDENCE_THRESHOLD, RuleResult, Severity
from app.schemas.response import ExtractionResponse
from app.rules.schedules import (
    category_has_schedule_data,
    is_unit_valid_for_type,
    permitted_qualifier_types,
)


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

def check_misleading_quantity_terms(response: ExtractionResponse) -> List[RuleResult]:
    """Rule 14: Misleading quantity terms (e.g. 'approximately', 'about',
    'up to', 'dozen') are prohibited.

    Each misleading term found produces one BLOCKING RuleResult.
    If the net quantity confidence is low or the field is uncertain, downgrade
    to NEEDS_REVIEW instead.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 14 "
        "(prohibition of misleading quantity expressions)"
    )
    results: List[RuleResult] = []

    if not response.misleadingQuantityTerms:
        results.append(_make_result(
            rule_id="rule_14_no_misleading_terms",
            reference=reference,
            description="No misleading quantity terms present",
            passed=True,
            severity=Severity.INFO,
            evidence_field="misleadingQuantityTerms",
            evidence_value="[]",
            evidence_confidence=None,
            source_image=None,
            message="No misleading quantity terms detected.",
        ))
        return results

    nq_confidence = response.netQuantity.confidence
    nq_uncertain = "netQuantity" in response.uncertainFields
    is_low_conf = nq_confidence < LOW_CONFIDENCE_THRESHOLD or nq_uncertain

    for term in response.misleadingQuantityTerms:
        if is_low_conf:
            results.append(_make_result(
                rule_id=f"rule_14_misleading_term_{term.text.lower().replace(' ', '_')}",
                reference=reference,
                description=f"Misleading quantity term: '{term.text}'",
                passed=True,
                severity=Severity.NEEDS_REVIEW,
                evidence_field="misleadingQuantityTerms",
                evidence_value=term.text,
                evidence_confidence=nq_confidence,
                source_image=term.sourceImage,
                message=(
                    f"Potential misleading term '{term.text}' detected, "
                    f"but net quantity has low confidence ({nq_confidence:.2f}). "
                    "Manual review recommended."
                ),
            ))
        else:
            results.append(_make_result(
                rule_id=f"rule_14_misleading_term_{term.text.lower().replace(' ', '_')}",
                reference=reference,
                description=f"Misleading quantity term prohibited: '{term.text}'",
                passed=False,
                severity=Severity.BLOCKING,
                evidence_field="misleadingQuantityTerms",
                evidence_value=term.text,
                evidence_confidence=nq_confidence,
                source_image=term.sourceImage,
                message=(
                    f"Prohibited misleading quantity term '{term.text}' found on label. "
                    "Rule 14 prohibits expressions such as 'approximately', 'about', 'up to', etc."
                ),
            ))

    return results


def check_quantity_qualifiers(response: ExtractionResponse) -> List[RuleResult]:
    """Rule 15: Quantity qualifiers (WHEN_PACKED, MINIMUM, NOT_LESS_THAN, etc.)
    are only permitted for specific commodity categories as defined in the schedules.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 15 "
        "(permitted quantity qualifiers by commodity category)"
    )
    results: List[RuleResult] = []

    if not response.quantityQualifiers:
        results.append(_make_result(
            rule_id="rule_15_no_qualifiers",
            reference=reference,
            description="No quantity qualifiers present on label",
            passed=True,
            severity=Severity.INFO,
            evidence_field="quantityQualifiers",
            evidence_value="[]",
            evidence_confidence=None,
            source_image=None,
            message="No quantity qualifiers detected.",
        ))
        return results

    category = response.commodity.category
    has_data = category_has_schedule_data(category)
    allowed = permitted_qualifier_types(category)

    for qualifier in response.quantityQualifiers:
        qt = qualifier.qualifierType
        rule_id = f"rule_15_qualifier_{qt.lower()}"

        if not has_data:
            # Can't validate — category has no schedule data
            results.append(_make_result(
                rule_id=rule_id,
                reference=reference,
                description=f"Qualifier type '{qt}' validity for category '{category}'",
                passed=True,
                severity=Severity.NEEDS_REVIEW,
                evidence_field="quantityQualifiers",
                evidence_value=f"{qualifier.text!r} (type={qt})",
                evidence_confidence=None,
                source_image=qualifier.sourceImage,
                message=(
                    f"Quantity qualifier '{qualifier.text}' (type={qt}) found. "
                    f"Cannot validate for category '{category}' — no Schedule 2/3 data. "
                    "Manual review required."
                ),
            ))
        elif qt in allowed:
            results.append(_make_result(
                rule_id=rule_id,
                reference=reference,
                description=f"Qualifier type '{qt}' permitted for category '{category}'",
                passed=True,
                severity=Severity.INFO,
                evidence_field="quantityQualifiers",
                evidence_value=f"{qualifier.text!r} (type={qt})",
                evidence_confidence=None,
                source_image=qualifier.sourceImage,
                message=(
                    f"Qualifier '{qualifier.text}' (type={qt}) is permitted "
                    f"for category '{category}'."
                ),
            ))
        else:
            results.append(_make_result(
                rule_id=rule_id,
                reference=reference,
                description=f"Qualifier type '{qt}' not permitted for category '{category}'",
                passed=False,
                severity=Severity.BLOCKING,
                evidence_field="quantityQualifiers",
                evidence_value=f"{qualifier.text!r} (type={qt})",
                evidence_confidence=None,
                source_image=qualifier.sourceImage,
                message=(
                    f"Quantity qualifier '{qualifier.text}' (type={qt}) is NOT permitted "
                    f"for category '{category}'. "
                    f"Permitted types: {sorted(allowed) or 'none'}."
                ),
            ))

    return results


def check_unit_validity(response: ExtractionResponse) -> RuleResult:
    """Rule 13: Net quantity must be expressed in SI units appropriate to the
    quantity type (weight/volume/length/count).

    This validates the unit the extraction layer produced — even though the
    classifier should already normalise to SI, an independent check here means
    the rules engine doesn't blindly trust upstream data it can check itself.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 13 "
        "(SI units for net quantity declaration)"
    )
    description = "Net quantity expressed in SI unit appropriate to quantity type"
    rule_id = "rule_13_unit_validity"

    nq = response.netQuantity
    if not nq.found:
        # No net quantity — already flagged by Rule 6; skip here
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.INFO,
            evidence_field="netQuantity",
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message="Net quantity not found — unit validation skipped (see Rule 6 check).",
        )

    unit = nq.unit
    qty_type = nq.quantityType

    if not unit:
        # Unit missing from extracted net quantity
        if nq.confidence < LOW_CONFIDENCE_THRESHOLD or "netQuantity" in response.uncertainFields:
            return _make_result(
                rule_id, reference, description,
                passed=True, severity=Severity.NEEDS_REVIEW,
                evidence_field="netQuantity.unit",
                evidence_value=None,
                evidence_confidence=nq.confidence,
                source_image=nq.sourceImage,
                message=(
                    "Net quantity unit not extracted and confidence is low. "
                    "Cannot validate unit — manual review required."
                ),
            )
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="netQuantity.unit",
            evidence_value=None,
            evidence_confidence=nq.confidence,
            source_image=nq.sourceImage,
            message="Net quantity unit is missing from the extracted data.",
        )

    # Validate unit against quantity type
    if not is_unit_valid_for_type(unit, qty_type):
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="netQuantity.unit",
            evidence_value=f"unit={unit!r}, quantityType={qty_type!r}",
            evidence_confidence=nq.confidence,
            source_image=nq.sourceImage,
            message=(
                f"Unit '{unit}' does not match quantity type '{qty_type}'. "
                "Net quantity must be expressed in an SI unit appropriate to the declared type."
            ),
        )

    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field="netQuantity.unit",
        evidence_value=f"unit={unit!r}, quantityType={qty_type!r}",
        evidence_confidence=nq.confidence,
        source_image=nq.sourceImage,
        message=f"Net quantity unit '{unit}' is valid for quantity type '{qty_type}'.",
    )


# ---------------------------------------------------------------------------
# Public: run all Rules 11–17 checks
# ---------------------------------------------------------------------------

def evaluate_rules_11_17(response: ExtractionResponse) -> List[RuleResult]:
    """Run all Rules 11–17 quantity checks and return a flat list of RuleResults."""
    results: List[RuleResult] = []
    results.extend(check_misleading_quantity_terms(response))
    results.extend(check_quantity_qualifiers(response))
    results.append(check_unit_validity(response))
    return results
