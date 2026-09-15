"""
app/rules/rule_6_mandatory.py — Rule 6 mandatory declaration presence checks.

Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6
Every package of commodities shall bear the following declarations:
  (a) Name of commodity
  (b) Name and address of manufacturer/packer/importer
  (c) Net quantity
  (d) Month and year of manufacture/packing
  (e) Maximum Retail Price (MRP)
  (f) Consumer care / complaint information

Rule 6 also requires dimensions for certain commodity categories
(garments, tyres, cables, etc.) — checked via schedules.py lookup.

TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15

ARCHITECTURAL RULE: this module imports ONLY from:
  - app.schemas.response   (ExtractionResponse and field models)
  - app.schemas.compliance (RuleResult, Severity)
  - app.rules.schedules    (dimensions_required lookup)
  NO imports from app.ocr, app.preprocessing, or app.classification.
"""

from __future__ import annotations

from typing import List

from app.schemas.compliance import LOW_CONFIDENCE_THRESHOLD, RuleResult, Severity
from app.schemas.response import ExtractionResponse
from app.rules.schedules import dimensions_required


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_low_confidence(confidence: float, field_name: str, response: ExtractionResponse) -> bool:
    """Return True if confidence is below threshold or the field is listed in
    uncertainFields — either condition triggers a NEEDS_REVIEW downgrade."""
    return (
        confidence < LOW_CONFIDENCE_THRESHOLD
        or field_name in response.uncertainFields
    )


def _make_result(
    rule_id: str,
    reference: str,
    description: str,
    passed: bool,
    severity: Severity,
    evidence_field: str | None,
    evidence_value: str | None,
    evidence_confidence: float | None,
    source_image: str | None,
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
# Individual checks — each returns exactly one RuleResult
# ---------------------------------------------------------------------------

def check_commodity_identity(response: ExtractionResponse) -> RuleResult:
    """Rule 6(1)(a) — Commodity name/identity must be declared on the label.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_commodity_identity"
    reference = "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(a)"
    description = "Commodity identity (name/category) is declared on the label"

    commodity = response.commodity
    if not commodity.found:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="commodity",
            evidence_value=None,
            evidence_confidence=commodity.confidence,
            source_image=commodity.sourceImage,
            message="Commodity identity not found on label.",
        )

    if _is_low_confidence(commodity.confidence, "commodity", response):
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.NEEDS_REVIEW,
            evidence_field="commodity",
            evidence_value=commodity.name or commodity.category,
            evidence_confidence=commodity.confidence,
            source_image=commodity.sourceImage,
            message=(
                f"Commodity found but with low confidence "
                f"({commodity.confidence:.2f} < {LOW_CONFIDENCE_THRESHOLD}). "
                "Manual review recommended."
            ),
        )

    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field="commodity",
        evidence_value=commodity.name or commodity.category,
        evidence_confidence=commodity.confidence,
        source_image=commodity.sourceImage,
        message=f"Commodity identity found: {commodity.name or commodity.category!r}.",
    )


def check_party_declaration(response: ExtractionResponse) -> RuleResult:
    """Rule 6(1)(b) — At least one of manufacturer/packer/importer must be
    present with BOTH name and address.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_party_declaration"
    reference = "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(b)"
    description = (
        "At least one of manufacturer/packer/importer with name AND address is declared"
    )

    parties = {
        "manufacturer": response.manufacturer,
        "packer": response.packer,
        "importer": response.importer,
    }

    # Collect parties found with both name and address
    complete_parties = []
    low_conf_parties = []

    for role, party in parties.items():
        if party.found and party.name and party.address:
            if _is_low_confidence(party.confidence, role, response):
                low_conf_parties.append((role, party))
            else:
                complete_parties.append((role, party))

    if complete_parties:
        role, party = complete_parties[0]
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.INFO,
            evidence_field=role,
            evidence_value=f"{party.name} / {party.address}",
            evidence_confidence=party.confidence,
            source_image=party.sourceImage,
            message=f"{role.capitalize()} with name and address found: {party.name!r}.",
        )

    if low_conf_parties:
        role, party = low_conf_parties[0]
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.NEEDS_REVIEW,
            evidence_field=role,
            evidence_value=f"{party.name} / {party.address}",
            evidence_confidence=party.confidence,
            source_image=party.sourceImage,
            message=(
                f"{role.capitalize()} found but with low confidence "
                f"({party.confidence:.2f}). Manual review recommended."
            ),
        )

    # Check for parties found but missing name or address
    partial_parties = [
        role for role, p in parties.items() if p.found and (p.name or p.address)
    ]
    if partial_parties:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field=partial_parties[0],
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message=(
                f"Party found ({', '.join(partial_parties)}) but name or address is incomplete. "
                "Both name and address are required."
            ),
        )

    return _make_result(
        rule_id, reference, description,
        passed=False, severity=Severity.BLOCKING,
        evidence_field=None,
        evidence_value=None,
        evidence_confidence=None,
        source_image=None,
        message=(
            "No manufacturer, packer, or importer with both name and address found on label."
        ),
    )


def check_net_quantity(response: ExtractionResponse) -> RuleResult:
    """Rule 6(1)(c) — Net quantity must be declared.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_net_quantity"
    reference = "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(c)"
    description = "Net quantity is declared on the label"

    nq = response.netQuantity
    if not nq.found:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="netQuantity",
            evidence_value=None,
            evidence_confidence=nq.confidence,
            source_image=nq.sourceImage,
            message="Net quantity not found on label.",
        )

    if _is_low_confidence(nq.confidence, "netQuantity", response):
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.NEEDS_REVIEW,
            evidence_field="netQuantity",
            evidence_value=nq.rawValue,
            evidence_confidence=nq.confidence,
            source_image=nq.sourceImage,
            message=(
                f"Net quantity found but with low confidence ({nq.confidence:.2f}). "
                "Manual review recommended."
            ),
        )

    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field="netQuantity",
        evidence_value=nq.rawValue,
        evidence_confidence=nq.confidence,
        source_image=nq.sourceImage,
        message=f"Net quantity found: {nq.rawValue!r}.",
    )


def check_date_of_manufacture_or_packing(response: ExtractionResponse) -> RuleResult:
    """Rule 6(1)(d) — Month and year of manufacture OR packing must be declared.

    Real labels use either manufacturing date OR packing date (sometimes both).
    Both date fields exist in the schema specifically for this reason.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_date_manufacture_or_packing"
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(d)"
    )
    description = "Month and year of manufacture or packing is declared"

    mfg = response.manufacturingDate
    pkg = response.packingDate

    # Prefer the one with higher confidence
    candidates = []
    if mfg.found:
        candidates.append(("manufacturingDate", mfg))
    if pkg.found:
        candidates.append(("packingDate", pkg))

    if not candidates:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field=None,
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message="Neither manufacturing date nor packing date found on label.",
        )

    # Sort by confidence descending; pick best
    candidates.sort(key=lambda x: x[1].confidence, reverse=True)
    field_name, best = candidates[0]

    if _is_low_confidence(best.confidence, field_name, response):
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.NEEDS_REVIEW,
            evidence_field=field_name,
            evidence_value=best.raw,
            evidence_confidence=best.confidence,
            source_image=best.sourceImage,
            message=(
                f"Date field ({field_name}) found but with low confidence "
                f"({best.confidence:.2f}). Manual review recommended."
            ),
        )

    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field=field_name,
        evidence_value=best.raw,
        evidence_confidence=best.confidence,
        source_image=best.sourceImage,
        message=f"Date of manufacture/packing found: {best.raw!r} ({field_name}).",
    )


def check_mrp(response: ExtractionResponse) -> RuleResult:
    """Rule 6(1)(e) — Maximum Retail Price (MRP) including all taxes must be declared.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_mrp"
    reference = "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(e)"
    description = "Maximum Retail Price (MRP) is declared on the label"

    mrp = response.mrp
    if not mrp.found:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="mrp",
            evidence_value=None,
            evidence_confidence=mrp.confidence,
            source_image=mrp.sourceImage,
            message="MRP not found on label.",
        )

    if _is_low_confidence(mrp.confidence, "mrp", response):
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.NEEDS_REVIEW,
            evidence_field="mrp",
            evidence_value=mrp.raw,
            evidence_confidence=mrp.confidence,
            source_image=mrp.sourceImage,
            message=(
                f"MRP found but with low confidence ({mrp.confidence:.2f}). "
                "Manual review recommended."
            ),
        )

    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field="mrp",
        evidence_value=mrp.raw or str(mrp.value),
        evidence_confidence=mrp.confidence,
        source_image=mrp.sourceImage,
        message=f"MRP found: {mrp.raw or mrp.value!r}.",
    )


def check_consumer_care(response: ExtractionResponse) -> RuleResult:
    """Rule 6(1)(f) — Consumer complaint/care information must be provided.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_consumer_care"
    reference = "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(f)"
    description = "Consumer care / complaint contact information is declared"

    cc = response.consumerCare
    if not cc.found:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="consumerCare",
            evidence_value=None,
            evidence_confidence=cc.confidence,
            source_image=cc.sourceImage,
            message="Consumer care / complaint contact information not found on label.",
        )

    if _is_low_confidence(cc.confidence, "consumerCare", response):
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.NEEDS_REVIEW,
            evidence_field="consumerCare",
            evidence_value=cc.phone or cc.email or cc.address,
            evidence_confidence=cc.confidence,
            source_image=cc.sourceImage,
            message=(
                f"Consumer care found but with low confidence ({cc.confidence:.2f}). "
                "Manual review recommended."
            ),
        )

    contact = cc.phone or cc.email or cc.address or "(details found)"
    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field="consumerCare",
        evidence_value=contact,
        evidence_confidence=cc.confidence,
        source_image=cc.sourceImage,
        message=f"Consumer care information found: {contact!r}.",
    )


def check_dimensions(response: ExtractionResponse) -> RuleResult:
    """Rule 6 + Fourth Schedule — Dimensions required for specific categories
    (garments, tyres, cables, etc.).

    If dimensions are not applicable for the category, emits INFO.
    If applicable but missing, emits BLOCKING.

    TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
    """
    rule_id = "rule_6_dimensions"
    reference = (
        "Legal Metrology (Packaged Commodities) Rules, 2011 — "
        "Rule 6 read with Fourth Schedule"
    )
    description = "Dimensions declared where required by commodity category"

    category = response.commodity.category
    required = dimensions_required(category)

    if not required:
        reason = (
            f"Dimensions not required for category {category!r}."
            if category
            else "Category unknown — dimensions requirement not determined."
        )
        return _make_result(
            rule_id, reference, description,
            passed=True, severity=Severity.INFO,
            evidence_field="commodity.category",
            evidence_value=category,
            evidence_confidence=None,
            source_image=None,
            message=reason,
        )

    # Dimensions are required — check they are present
    if not response.dimensions:
        return _make_result(
            rule_id, reference, description,
            passed=False, severity=Severity.BLOCKING,
            evidence_field="dimensions",
            evidence_value=None,
            evidence_confidence=None,
            source_image=None,
            message=(
                f"Dimensions are required for category {category!r} "
                "but not found on label."
            ),
        )

    dim_summary = ", ".join(
        f"{d.label}={d.value}{d.unit}" for d in response.dimensions if d.value
    )
    return _make_result(
        rule_id, reference, description,
        passed=True, severity=Severity.INFO,
        evidence_field="dimensions",
        evidence_value=dim_summary or "(dimensions found)",
        evidence_confidence=None,
        source_image=response.dimensions[0].sourceImage,
        message=f"Dimensions found for {category!r}: {dim_summary or 'present'}.",
    )


# ---------------------------------------------------------------------------
# Public: run all Rule 6 checks
# ---------------------------------------------------------------------------

def evaluate_rule_6(response: ExtractionResponse) -> List[RuleResult]:
    """Run all Rule 6 checks and return one RuleResult per check."""
    return [
        check_commodity_identity(response),
        check_party_declaration(response),
        check_net_quantity(response),
        check_date_of_manufacture_or_packing(response),
        check_mrp(response),
        check_consumer_care(response),
        check_dimensions(response),
    ]
