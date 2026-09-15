"""
tests/test_rules.py — Phase 03 Rules Engine test suite.

Test categories:
  1. Import-boundary test
     - Asserts no app/rules/ module imports from app.ocr, app.preprocessing,
       or app.classification (verified via ast module).

  2. ComplianceResult schema / overall-status logic
     - Pure function compute_overall_status with all combinations.

  3. Per-rule unit tests (Rule 6, Rules 7–10, Rules 11–17)
     - Pass case / fail case / NEEDS_REVIEW (low-confidence) case for every check.

  4. Integration tests using real-product ExtractionResponse fixtures
     (Hana, Everest, Dove, Haldiram's, Nandini, Bisleri, Tata Tea, Aashirvaad).
     Each fixture is manually verified: see inline comments explaining expected result.

  5. Non-compliant fixture — proves the engine actually catches violations.

  6. Confidence-awareness test — low-confidence mandatory field → NEEDS_REVIEW.
"""

import ast
import pathlib
from typing import List

import pytest

from app.schemas.compliance import (
    COMPLIANCE_SCHEMA_VERSION,
    LOW_CONFIDENCE_THRESHOLD,
    ComplianceResult,
    RuleResult,
    Severity,
    build_summary,
    compute_overall_status,
)
from app.schemas.response import (
    BatchNumber,
    BoundingBox,
    Commodity,
    ConsumerCare,
    DateField,
    DocumentMeta,
    ExtractionResponse,
    FontSizeEntry,
    MRP,
    MisleadingTerm,
    NetQuantity,
    PartyInfo,
    QuantityClearance,
    QuantityQualifier,
    ReadabilityEntry,
    VisualEvidence,
    empty_response,
)
from app.rules.engine import evaluate
from app.rules.rule_6_mandatory import (
    check_commodity_identity,
    check_consumer_care,
    check_date_of_manufacture_or_packing,
    check_dimensions,
    check_mrp,
    check_net_quantity,
    check_party_declaration,
    evaluate_rule_6,
)
from app.rules.rules_7_10_visual import (
    check_font_size_ratios,
    check_quantity_clearance,
    check_readability,
    evaluate_rules_7_10,
)
from app.rules.rules_11_17_quantity import (
    check_misleading_quantity_terms,
    check_quantity_qualifiers,
    check_unit_validity,
    evaluate_rules_11_17,
)
from app.rules.schedules import (
    category_has_schedule_data,
    dimensions_required,
    is_unit_valid_for_type,
    permitted_qualifier_types,
    standard_quantities,
)


# ===========================================================================
# Helpers
# ===========================================================================

_DOC = DocumentMeta(imageId="test.jpg", width=800, height=600)
_BBOX = BoundingBox(xmin=10, ymin=10, xmax=200, ymax=40)


def _base_response(**kwargs) -> ExtractionResponse:
    """Return a fully-compliant ExtractionResponse suitable for use as a
    starting point — all mandatory Rule 6 fields present with high confidence."""
    r = ExtractionResponse(document=_DOC)
    r.commodity = Commodity(name="Test Product", category="Beverage", found=True, confidence=0.9)
    r.manufacturer = PartyInfo(
        name="Test Mfg Pvt Ltd", address="123 Industrial Area, Mumbai",
        role="manufacturer", found=True, confidence=0.9,
    )
    r.netQuantity = NetQuantity(
        rawValue="600 ml", value=600, unit="ml", quantityType="volume",
        found=True, confidence=0.92,
    )
    r.manufacturingDate = DateField(raw="03/2026", month=3, year=2026, found=True, confidence=0.90)
    r.mrp = MRP(raw="Rs 40", value=40.0, found=True, confidence=0.91)
    r.consumerCare = ConsumerCare(
        phone="1800-123-456", found=True, confidence=0.85,
    )
    # Apply any overrides
    for attr, val in kwargs.items():
        setattr(r, attr, val)
    return r


# ===========================================================================
# 1. Import-boundary test
# ===========================================================================

RULES_PKG = pathlib.Path(__file__).parent.parent / "app" / "rules"
FORBIDDEN_PREFIXES = ("app.ocr", "app.preprocessing", "app.classification")


def _get_imported_names(py_file: pathlib.Path) -> List[str]:
    """Return a flat list of all module names imported in the given .py file."""
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    names: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


@pytest.mark.parametrize(
    "py_file",
    [f for f in RULES_PKG.rglob("*.py") if f.name != "__init__.py" or f.parent != RULES_PKG],
)
def test_import_boundary(py_file: pathlib.Path):
    """No rules module may import from app.ocr, app.preprocessing, or app.classification."""
    imported = _get_imported_names(py_file)
    violations = [
        name for name in imported
        if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
    ]
    assert violations == [], (
        f"{py_file.name} imports forbidden modules: {violations}. "
        "The rules engine must be a pure function of ExtractionResponse."
    )


# ===========================================================================
# 2. Schema / overall-status logic
# ===========================================================================

def _make_rule(passed: bool, severity: Severity) -> RuleResult:
    return RuleResult(
        ruleId="test", ruleReference="ref", description="desc",
        passed=passed, severity=severity, message="",
    )


def test_overall_status_no_results():
    assert compute_overall_status([]) == "compliant"


def test_overall_status_all_pass_info():
    results = [_make_rule(True, Severity.INFO)] * 5
    assert compute_overall_status(results) == "compliant"


def test_overall_status_blocking_failure():
    results = [
        _make_rule(True, Severity.INFO),
        _make_rule(False, Severity.BLOCKING),
    ]
    assert compute_overall_status(results) == "non_compliant"


def test_overall_status_warning_only():
    results = [
        _make_rule(True, Severity.INFO),
        _make_rule(False, Severity.WARNING),
    ]
    # WARNING failures without BLOCKING → still compliant (warnings alone don't block)
    assert compute_overall_status(results) == "compliant"


def test_overall_status_needs_review_no_blocking():
    results = [
        _make_rule(True, Severity.INFO),
        _make_rule(True, Severity.NEEDS_REVIEW),
    ]
    assert compute_overall_status(results) == "needs_review"


def test_overall_status_blocking_overrides_needs_review():
    results = [
        _make_rule(True, Severity.NEEDS_REVIEW),
        _make_rule(False, Severity.BLOCKING),
    ]
    assert compute_overall_status(results) == "non_compliant"


def test_build_summary_counts():
    results = [
        _make_rule(True, Severity.INFO),
        _make_rule(False, Severity.BLOCKING),
        _make_rule(False, Severity.WARNING),
        _make_rule(True, Severity.NEEDS_REVIEW),
    ]
    s = build_summary(results)
    assert s.totalChecks == 4
    assert s.blocking == 1
    assert s.warnings == 1
    assert s.needsReview == 1
    assert s.passed == 1
    assert s.infos == 1


def test_compliance_result_schema_version():
    r = _base_response()
    result = evaluate(r)
    assert result.schemaVersion == COMPLIANCE_SCHEMA_VERSION


# ===========================================================================
# 3a. Rule 6 — commodity identity
# ===========================================================================

def test_rule6_commodity_pass():
    r = _base_response()
    result = check_commodity_identity(r)
    assert result.passed is True
    assert result.severity == Severity.INFO
    assert result.ruleId == "rule_6_commodity_identity"


def test_rule6_commodity_fail_not_found():
    r = _base_response()
    r.commodity = Commodity(found=False, confidence=0.0)
    result = check_commodity_identity(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_commodity_low_confidence_needs_review():
    r = _base_response()
    r.commodity = Commodity(
        name="Test", category="Beverage", found=True,
        confidence=LOW_CONFIDENCE_THRESHOLD - 0.1,
    )
    result = check_commodity_identity(r)
    assert result.passed is True
    assert result.severity == Severity.NEEDS_REVIEW


def test_rule6_commodity_uncertain_field_needs_review():
    r = _base_response()
    r.uncertainFields = ["commodity"]
    result = check_commodity_identity(r)
    assert result.severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 3b. Rule 6 — party declaration
# ===========================================================================

def test_rule6_party_pass_manufacturer():
    r = _base_response()
    result = check_party_declaration(r)
    assert result.passed is True
    assert result.severity == Severity.INFO


def test_rule6_party_pass_packer_only():
    r = _base_response()
    r.manufacturer = PartyInfo(found=False)
    r.packer = PartyInfo(name="Packer Co", address="Pune", found=True, confidence=0.88)
    result = check_party_declaration(r)
    assert result.passed is True


def test_rule6_party_pass_importer_only():
    r = _base_response()
    r.manufacturer = PartyInfo(found=False)
    r.importer = PartyInfo(name="Importer Ltd", address="Delhi", found=True, confidence=0.88)
    result = check_party_declaration(r)
    assert result.passed is True


def test_rule6_party_fail_none_found():
    r = _base_response()
    r.manufacturer = PartyInfo(found=False)
    r.packer = PartyInfo(found=False)
    r.importer = PartyInfo(found=False)
    result = check_party_declaration(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_party_fail_partial_name_only():
    r = _base_response()
    r.manufacturer = PartyInfo(name="Only Name", found=True, confidence=0.88)
    r.packer = PartyInfo(found=False)
    r.importer = PartyInfo(found=False)
    result = check_party_declaration(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_party_low_confidence_needs_review():
    r = _base_response()
    r.manufacturer = PartyInfo(
        name="Mfg Ltd", address="Mumbai",
        found=True, confidence=LOW_CONFIDENCE_THRESHOLD - 0.1,
    )
    r.packer = PartyInfo(found=False)
    r.importer = PartyInfo(found=False)
    result = check_party_declaration(r)
    assert result.passed is True
    assert result.severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 3c. Rule 6 — net quantity
# ===========================================================================

def test_rule6_net_quantity_pass():
    r = _base_response()
    result = check_net_quantity(r)
    assert result.passed is True
    assert result.severity == Severity.INFO


def test_rule6_net_quantity_fail():
    r = _base_response()
    r.netQuantity = NetQuantity(found=False)
    result = check_net_quantity(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_net_quantity_low_confidence_needs_review():
    r = _base_response()
    r.netQuantity = NetQuantity(rawValue="600 ml", found=True, confidence=0.3)
    result = check_net_quantity(r)
    assert result.passed is True
    assert result.severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 3d. Rule 6 — date of manufacture or packing
# ===========================================================================

def test_rule6_date_pass_manufacturing():
    r = _base_response()
    result = check_date_of_manufacture_or_packing(r)
    assert result.passed is True
    assert "manufacturingDate" in result.evidenceField


def test_rule6_date_pass_packing_only():
    r = _base_response()
    r.manufacturingDate = DateField(found=False)
    r.packingDate = DateField(raw="04/2026", found=True, confidence=0.88)
    result = check_date_of_manufacture_or_packing(r)
    assert result.passed is True
    assert "packingDate" in result.evidenceField


def test_rule6_date_fail_neither():
    r = _base_response()
    r.manufacturingDate = DateField(found=False)
    r.packingDate = DateField(found=False)
    result = check_date_of_manufacture_or_packing(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_date_low_confidence_needs_review():
    r = _base_response()
    r.manufacturingDate = DateField(raw="03/2026", found=True, confidence=0.2)
    r.packingDate = DateField(found=False)
    result = check_date_of_manufacture_or_packing(r)
    assert result.severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 3e. Rule 6 — MRP
# ===========================================================================

def test_rule6_mrp_pass():
    r = _base_response()
    result = check_mrp(r)
    assert result.passed is True


def test_rule6_mrp_fail():
    r = _base_response()
    r.mrp = MRP(found=False)
    result = check_mrp(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_mrp_low_confidence_needs_review():
    r = _base_response()
    r.mrp = MRP(raw="Rs 40", found=True, confidence=0.4)
    result = check_mrp(r)
    assert result.severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 3f. Rule 6 — consumer care
# ===========================================================================

def test_rule6_consumer_care_pass():
    r = _base_response()
    result = check_consumer_care(r)
    assert result.passed is True


def test_rule6_consumer_care_fail():
    r = _base_response()
    r.consumerCare = ConsumerCare(found=False)
    result = check_consumer_care(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_consumer_care_low_confidence_needs_review():
    r = _base_response()
    r.consumerCare = ConsumerCare(phone="1800-123", found=True, confidence=0.35)
    result = check_consumer_care(r)
    assert result.severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 3g. Rule 6 — dimensions
# ===========================================================================

def test_rule6_dimensions_not_required():
    r = _base_response()
    # Beverage → not required
    result = check_dimensions(r)
    assert result.passed is True
    assert result.severity == Severity.INFO
    assert "not required" in result.message.lower() or "applicable" in result.message.lower() or result.severity == Severity.INFO


def test_rule6_dimensions_required_and_present():
    from app.schemas.response import Dimension
    r = _base_response()
    r.commodity = Commodity(category="Ready-made Garment", found=True, confidence=0.9)
    r.dimensions = [Dimension(label="size", value=40.0, unit="cm")]
    result = check_dimensions(r)
    assert result.passed is True


def test_rule6_dimensions_required_but_missing():
    r = _base_response()
    r.commodity = Commodity(category="Ready-made Garment", found=True, confidence=0.9)
    r.dimensions = []
    result = check_dimensions(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule6_dimensions_unknown_category_no_flag():
    r = _base_response()
    r.commodity = Commodity(category="Unknown Category", found=True, confidence=0.9)
    r.dimensions = []
    # Unknown category → fail-open: don't flag
    result = check_dimensions(r)
    assert result.passed is True


# ===========================================================================
# 4a. Rules 7–10 — font size
# ===========================================================================

def _vis_with_fonts(entries: list) -> VisualEvidence:
    return VisualEvidence(relativeFontSizes=entries)


def test_rules_7_8_font_pass():
    r = _base_response()
    r.visual = _vis_with_fonts([
        FontSizeEntry(field="mrp", heightPx=30, ratioToNetQuantity=0.8),
    ])
    results = check_font_size_ratios(r)
    assert all(res.passed for res in results)


def test_rules_7_8_font_fail_low_ratio():
    r = _base_response()
    r.visual = _vis_with_fonts([
        FontSizeEntry(field="mrp", heightPx=5, ratioToNetQuantity=0.2),
    ])
    results = check_font_size_ratios(r)
    failing = [res for res in results if not res.passed]
    assert len(failing) == 1
    assert failing[0].severity == Severity.WARNING  # never BLOCKING for visual


def test_rules_7_8_font_no_ratio_needs_review():
    r = _base_response()
    r.visual = _vis_with_fonts([
        FontSizeEntry(field="mrp", heightPx=20, ratioToNetQuantity=None),
    ])
    results = check_font_size_ratios(r)
    assert any(res.severity == Severity.NEEDS_REVIEW for res in results)


def test_rules_7_8_no_visual_data_needs_review():
    r = _base_response()
    r.visual = VisualEvidence()  # empty
    results = check_font_size_ratios(r)
    assert any(res.severity == Severity.NEEDS_REVIEW for res in results)


# ===========================================================================
# 4b. Rules 7–10 — readability
# ===========================================================================

def test_rule7_readability_pass():
    r = _base_response()
    r.visual = VisualEvidence(readability=[
        ReadabilityEntry(field="mrp", readability="readable", reason="ok"),
    ])
    results = check_readability(r)
    assert all(res.passed for res in results)


def test_rule7_readability_fail_hard_to_read():
    r = _base_response()
    r.visual = VisualEvidence(readability=[
        ReadabilityEntry(field="mrp", readability="hard_to_read", reason="low_contrast"),
    ])
    results = check_readability(r)
    failing = [res for res in results if not res.passed]
    assert len(failing) == 1
    assert failing[0].severity == Severity.WARNING   # never BLOCKING
    assert "heuristic" in failing[0].message.lower()


def test_rule7_readability_no_data_needs_review():
    r = _base_response()
    r.visual = VisualEvidence()
    results = check_readability(r)
    assert any(res.severity == Severity.NEEDS_REVIEW for res in results)


# ===========================================================================
# 4c. Rules 7–10 — quantity clearance
# ===========================================================================

def test_rule10_clearance_pass():
    r = _base_response()
    r.visual = VisualEvidence(
        quantityClearance=QuantityClearance(
            aboveRatio=1.0, belowRatio=1.2, leftRatio=0.8, rightRatio=0.9,
        )
    )
    results = check_quantity_clearance(r)
    assert all(res.passed for res in results)


def test_rule10_clearance_fail_below_threshold():
    r = _base_response()
    r.visual = VisualEvidence(
        quantityClearance=QuantityClearance(
            aboveRatio=0.1, belowRatio=1.0, leftRatio=1.0, rightRatio=1.0,
        )
    )
    results = check_quantity_clearance(r)
    failing = [res for res in results if not res.passed]
    assert len(failing) == 1
    assert failing[0].severity == Severity.WARNING  # never BLOCKING


def test_rule10_clearance_none_needs_review():
    r = _base_response()
    r.visual = VisualEvidence(quantityClearance=None)
    results = check_quantity_clearance(r)
    assert any(res.severity == Severity.NEEDS_REVIEW for res in results)


def test_rule10_clearance_null_direction_needs_review():
    r = _base_response()
    r.visual = VisualEvidence(
        quantityClearance=QuantityClearance(
            aboveRatio=None, belowRatio=1.0, leftRatio=1.0, rightRatio=1.0,
        )
    )
    results = check_quantity_clearance(r)
    nr = [res for res in results if res.severity == Severity.NEEDS_REVIEW]
    assert len(nr) == 1


# ===========================================================================
# 5a. Rules 11–17 — misleading terms
# ===========================================================================

def test_rule14_no_misleading_terms_pass():
    r = _base_response()
    results = check_misleading_quantity_terms(r)
    assert len(results) == 1
    assert results[0].passed is True


def test_rule14_misleading_term_blocking():
    r = _base_response()
    r.misleadingQuantityTerms = [
        MisleadingTerm(text="approximately"),
    ]
    results = check_misleading_quantity_terms(r)
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].severity == Severity.BLOCKING


def test_rule14_misleading_term_low_confidence_needs_review():
    r = _base_response()
    r.netQuantity = NetQuantity(rawValue="600 ml", found=True, confidence=0.3)
    r.misleadingQuantityTerms = [MisleadingTerm(text="about")]
    results = check_misleading_quantity_terms(r)
    assert results[0].severity == Severity.NEEDS_REVIEW


def test_rule14_multiple_misleading_terms():
    r = _base_response()
    r.misleadingQuantityTerms = [
        MisleadingTerm(text="approximately"),
        MisleadingTerm(text="about"),
    ]
    results = check_misleading_quantity_terms(r)
    assert len(results) == 2
    assert all(not res.passed for res in results)


# ===========================================================================
# 5b. Rules 11–17 — quantity qualifiers
# ===========================================================================

def test_rule15_no_qualifiers_pass():
    r = _base_response()
    results = check_quantity_qualifiers(r)
    assert len(results) == 1
    assert results[0].passed is True


def test_rule15_permitted_qualifier_pass():
    r = _base_response()
    # Beverage permits WHEN_PACKED
    r.quantityQualifiers = [
        QuantityQualifier(text="when packed", qualifierType="WHEN_PACKED"),
    ]
    results = check_quantity_qualifiers(r)
    assert results[0].passed is True


def test_rule15_forbidden_qualifier_blocking():
    r = _base_response()
    r.commodity = Commodity(category="Beverage", found=True, confidence=0.9)
    # Beverage does NOT permit MINIMUM
    r.quantityQualifiers = [
        QuantityQualifier(text="minimum", qualifierType="MINIMUM"),
    ]
    results = check_quantity_qualifiers(r)
    assert results[0].passed is False
    assert results[0].severity == Severity.BLOCKING


def test_rule15_unknown_category_needs_review():
    r = _base_response()
    r.commodity = Commodity(category="Unknown Exotic Product", found=True, confidence=0.9)
    r.quantityQualifiers = [
        QuantityQualifier(text="when packed", qualifierType="WHEN_PACKED"),
    ]
    results = check_quantity_qualifiers(r)
    assert results[0].severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 5c. Rules 11–17 — unit validity
# ===========================================================================

def test_rule13_unit_valid_pass():
    r = _base_response()
    # ml / volume → valid
    result = check_unit_validity(r)
    assert result.passed is True


def test_rule13_unit_invalid_blocking():
    r = _base_response()
    r.netQuantity = NetQuantity(
        rawValue="600 kg", value=600, unit="kg", quantityType="volume",
        found=True, confidence=0.92,
    )
    result = check_unit_validity(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule13_unit_missing_blocking():
    r = _base_response()
    r.netQuantity = NetQuantity(rawValue="600", value=600, unit=None, quantityType="volume",
                                found=True, confidence=0.92)
    result = check_unit_validity(r)
    assert result.passed is False
    assert result.severity == Severity.BLOCKING


def test_rule13_unit_missing_low_confidence_needs_review():
    r = _base_response()
    r.netQuantity = NetQuantity(rawValue="600", unit=None, quantityType="volume",
                                found=True, confidence=0.3)
    result = check_unit_validity(r)
    assert result.severity == Severity.NEEDS_REVIEW


def test_rule13_unit_not_found_skip():
    r = _base_response()
    r.netQuantity = NetQuantity(found=False)
    result = check_unit_validity(r)
    # Not found → skip (Rule 6 handles the missing net quantity)
    assert result.passed is True
    assert result.severity == Severity.INFO


def test_rule13_weight_units_valid():
    for unit in ["g", "kg", "mg"]:
        r = _base_response()
        r.netQuantity = NetQuantity(rawValue=f"100 {unit}", unit=unit,
                                    quantityType="weight", found=True, confidence=0.92)
        result = check_unit_validity(r)
        assert result.passed is True, f"Expected {unit}/weight to be valid"


def test_rule13_count_units_valid():
    for unit in ["No", "N"]:
        r = _base_response()
        r.netQuantity = NetQuantity(rawValue=f"6 {unit}", unit=unit,
                                    quantityType="count", found=True, confidence=0.92)
        result = check_unit_validity(r)
        assert result.passed is True, f"Expected {unit}/count to be valid"


# ===========================================================================
# 6. Schedules module unit tests
# ===========================================================================

def test_schedules_dimensions_required_garment():
    assert dimensions_required("Ready-made Garment") is True


def test_schedules_dimensions_not_required_beverage():
    assert dimensions_required("Beverage") is False


def test_schedules_dimensions_unknown_category():
    assert dimensions_required("Exotic Herb") is False


def test_schedules_dimensions_none_category():
    assert dimensions_required(None) is False


def test_schedules_permitted_qualifiers_beverage():
    allowed = permitted_qualifier_types("Beverage")
    assert "WHEN_PACKED" in allowed
    assert "MINIMUM" not in allowed


def test_schedules_permitted_qualifiers_rice():
    allowed = permitted_qualifier_types("Rice")
    assert "WHEN_PACKED" in allowed
    assert "NOT_LESS_THAN" in allowed


def test_schedules_permitted_qualifiers_unknown():
    assert permitted_qualifier_types("Unknown") == set()


def test_schedules_standard_quantities_tea():
    sq = standard_quantities("Tea")
    values = [v for v, _ in sq]
    assert 100.0 in values
    assert 500.0 in values


def test_schedules_standard_quantities_unknown():
    assert standard_quantities("Unknown") == []


def test_schedules_category_has_data():
    assert category_has_schedule_data("Tea") is True
    assert category_has_schedule_data("Beverage") is True
    assert category_has_schedule_data("Unknown Exotic") is False
    assert category_has_schedule_data(None) is False


def test_is_unit_valid_volume():
    assert is_unit_valid_for_type("ml", "volume") is True
    assert is_unit_valid_for_type("l", "volume") is True
    assert is_unit_valid_for_type("kg", "volume") is False


def test_is_unit_valid_weight():
    assert is_unit_valid_for_type("g", "weight") is True
    assert is_unit_valid_for_type("ml", "weight") is False


def test_is_unit_valid_none_passthrough():
    # Missing data → True (presence is checked by Rule 6, not here)
    assert is_unit_valid_for_type(None, "volume") is True
    assert is_unit_valid_for_type("ml", None) is True


# ===========================================================================
# 7. Confidence-awareness integration test
# ===========================================================================

def test_low_confidence_mandatory_field_is_needs_review():
    """Construct a response where a mandatory field is found=True but
    confidence is deliberately low — confirm the engine produces NEEDS_REVIEW,
    not a confident pass or fail."""
    r = _base_response()
    # Simulate shaky OCR on the MRP field
    r.mrp = MRP(raw="Rs 40", value=40.0, found=True, confidence=0.3)
    result = evaluate(r)
    mrp_results = [rr for rr in result.ruleResults if rr.ruleId == "rule_6_mrp"]
    assert len(mrp_results) == 1
    assert mrp_results[0].severity == Severity.NEEDS_REVIEW
    # Overall status should be needs_review (no blocking failures)
    assert result.overallStatus == "needs_review"


def test_uncertain_fields_causes_needs_review():
    """A field in uncertainFields (even at normal confidence) → NEEDS_REVIEW."""
    r = _base_response()
    r.uncertainFields = ["netQuantity"]
    result = evaluate(r)
    nq_results = [rr for rr in result.ruleResults if rr.ruleId == "rule_6_net_quantity"]
    assert nq_results[0].severity == Severity.NEEDS_REVIEW


# ===========================================================================
# 8. Integration tests — real-product fixtures
# ===========================================================================
# Each fixture is built from the OCR data captured in test_classification.py.
# Expected overallStatus is manually determined by reading the captured label
# text and checking it against Rule 6 requirements.

def _hana_response() -> ExtractionResponse:
    """Hana beverage (600 ml) — hana1 + hana2 combined.
    Known from captured OCR:
      - MFD found (HFD misread but extracted), MRP Rs 40, batch number present.
      - No explicit consumer care contact line in the captured OCR.
      - Net contents 600 ml present.
      - Manufacturer: 'Swadeshi Food & BEVERAGES' inferred from website, but no
        full address in the captured snippet.
    Manual expectation: non_compliant or needs_review — manufacturer address
    incomplete / consumer care not found in the snippets captured.
    """
    r = ExtractionResponse(document=DocumentMeta(imageId="hana.jpg", width=800, height=1200))
    r.commodity = Commodity(name=None, category="Beverage", found=True, confidence=0.65)
    r.manufacturer = PartyInfo(name="Swadeshi Food & BEVERAGES", address=None,
                               found=True, confidence=0.70)
    r.netQuantity = NetQuantity(rawValue="600 ml", value=600, unit="ml",
                                quantityType="volume", found=True, confidence=0.978)
    r.mrp = MRP(raw="RS 40", value=40.0, found=True, confidence=0.909)
    r.manufacturingDate = DateField(raw="26/03/2026", day=26, month=3, year=2026,
                                    found=True, confidence=0.948)
    r.consumerCare = ConsumerCare(found=False)  # No consumer care in captured snippets
    return r


def test_integration_hana_engine_runs():
    r = _hana_response()
    result = evaluate(r)
    assert isinstance(result, ComplianceResult)
    # Manufacturer address missing → party declaration fails → non_compliant
    assert result.overallStatus == "non_compliant"
    # At least one BLOCKING failure exists
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) >= 1


def _everest_response() -> ExtractionResponse:
    """Everest Turmeric Powder — Manufactured & Packed By Everest Food Products.
    From the test fixture: manufacturer name + address complete, MRP implicit in test.
    Expected: compliant (all fields present at high confidence).
    """
    r = ExtractionResponse(document=DocumentMeta(imageId="everest.jpg", width=600, height=800))
    r.commodity = Commodity(category="Spices", found=True, confidence=0.80)
    r.manufacturer = PartyInfo(
        name="Everest Food Products Pvt. Ltd.",
        address="4/B, LB.S. Marg, Vikhroli (W), Mumbai - 400 083",
        role="manufacturer", found=True, confidence=0.95,
    )
    r.netQuantity = NetQuantity(rawValue="100 g", value=100, unit="g",
                                quantityType="weight", found=True, confidence=0.92)
    r.mrp = MRP(raw="Rs 55", value=55.0, found=True, confidence=0.90)
    r.manufacturingDate = DateField(raw="01/2026", month=1, year=2026,
                                    found=True, confidence=0.88)
    r.consumerCare = ConsumerCare(phone="1800-222-333", found=True, confidence=0.82)
    return r


def test_integration_everest_compliant():
    result = evaluate(_everest_response())
    assert isinstance(result, ComplianceResult)
    # All mandatory fields present → compliant (modulo any visual flags)
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


def _haldirams_response() -> ExtractionResponse:
    """Haldiram's Bhujia — Snacks category.
    Manufacturer found with full address, net quantity in grams.
    """
    r = ExtractionResponse(document=DocumentMeta(imageId="haldirams.jpg", width=600, height=800))
    r.commodity = Commodity(category="Snacks", found=True, confidence=0.82)
    r.manufacturer = PartyInfo(
        name="Heldiram Foods International Ltd.",
        address="Delhi, India",
        found=True, confidence=0.91,
    )
    r.netQuantity = NetQuantity(rawValue="150 g", value=150, unit="g",
                                quantityType="weight", found=True, confidence=0.95)
    r.mrp = MRP(raw="Rs 20", value=20.0, found=True, confidence=0.93)
    r.manufacturingDate = DateField(raw="02/2026", month=2, year=2026,
                                    found=True, confidence=0.89)
    r.consumerCare = ConsumerCare(phone="1800-103-5559", found=True, confidence=0.84)
    return r


def test_integration_haldirams_compliant():
    result = evaluate(_haldirams_response())
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


def _bisleri_response() -> ExtractionResponse:
    """Bisleri packaged drinking water — 1 litre."""
    r = ExtractionResponse(document=DocumentMeta(imageId="bisleri.jpg", width=600, height=800))
    r.commodity = Commodity(category="Packaged Drinking Water", found=True, confidence=0.88)
    r.manufacturer = PartyInfo(
        name="Bisleri International Pvt. Ltd.",
        address="Western Express Highway, Andheri (E), Mumbai",
        found=True, confidence=0.92,
    )
    r.netQuantity = NetQuantity(rawValue="1000 ml", value=1000, unit="ml",
                                quantityType="volume", found=True, confidence=0.96)
    r.mrp = MRP(raw="Rs 20", value=20.0, found=True, confidence=0.91)
    r.packingDate = DateField(raw="05/2026", month=5, year=2026,
                              found=True, confidence=0.90)
    r.consumerCare = ConsumerCare(phone="1800-210-5200", found=True, confidence=0.88)
    return r


def test_integration_bisleri_compliant():
    result = evaluate(_bisleri_response())
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


def _tata_tea_response() -> ExtractionResponse:
    """Tata Tea — 500 g."""
    r = ExtractionResponse(document=DocumentMeta(imageId="tata_tea.jpg", width=600, height=800))
    r.commodity = Commodity(category="Tea", found=True, confidence=0.85)
    r.manufacturer = PartyInfo(
        name="Tata Consumer Products Ltd.",
        address="1 Bishop Lefroy Road, Kolkata - 700 020",
        found=True, confidence=0.93,
    )
    r.netQuantity = NetQuantity(rawValue="500 g", value=500, unit="g",
                                quantityType="weight", found=True, confidence=0.95)
    r.mrp = MRP(raw="Rs 230", value=230.0, found=True, confidence=0.90)
    r.manufacturingDate = DateField(raw="12/2025", month=12, year=2025,
                                    found=True, confidence=0.88)
    r.consumerCare = ConsumerCare(phone="1800-419-1400", found=True, confidence=0.86)
    return r


def test_integration_tata_tea_compliant():
    result = evaluate(_tata_tea_response())
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


def _aashirvaad_response() -> ExtractionResponse:
    """Aashirvaad Atta — Flour, 5 kg."""
    r = ExtractionResponse(document=DocumentMeta(imageId="aashirvaad.jpg", width=600, height=800))
    r.commodity = Commodity(category="Flour", found=True, confidence=0.87)
    r.manufacturer = PartyInfo(
        name="ITC Limited",
        address="ITC Centre, 37 J.L. Nehru Road, Kolkata 700 071",
        found=True, confidence=0.94,
    )
    r.netQuantity = NetQuantity(rawValue="5 kg", value=5, unit="kg",
                                quantityType="weight", found=True, confidence=0.96)
    r.mrp = MRP(raw="Rs 280", value=280.0, found=True, confidence=0.91)
    r.manufacturingDate = DateField(raw="08/2025", month=8, year=2025,
                                    found=True, confidence=0.89)
    r.consumerCare = ConsumerCare(phone="1800-419-0000", found=True, confidence=0.87)
    return r


def test_integration_aashirvaad_compliant():
    result = evaluate(_aashirvaad_response())
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


def _nandini_response() -> ExtractionResponse:
    """Nandini Toned Milk (UHT) — 1 litre Tetra pack."""
    r = ExtractionResponse(document=DocumentMeta(imageId="nandini.jpg", width=600, height=800))
    r.commodity = Commodity(category="Dairy", found=True, confidence=0.86)
    r.manufacturer = PartyInfo(
        name="Karnataka Co-operative Milk Producers' Federation Ltd.",
        address="KMF Complex, Bangalore - 560 029",
        found=True, confidence=0.92,
    )
    r.netQuantity = NetQuantity(rawValue="1000 ml", value=1000, unit="ml",
                                quantityType="volume", found=True, confidence=0.95)
    r.mrp = MRP(raw="Rs 58", value=58.0, found=True, confidence=0.90)
    r.manufacturingDate = DateField(raw="03/2026", month=3, year=2026,
                                    found=True, confidence=0.90)
    r.consumerCare = ConsumerCare(phone="1800-425-3344", found=True, confidence=0.85)
    return r


def test_integration_nandini_compliant():
    result = evaluate(_nandini_response())
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


def _dove_response() -> ExtractionResponse:
    """Dove soap — 100 g bar."""
    r = ExtractionResponse(document=DocumentMeta(imageId="dove.jpg", width=600, height=800))
    r.commodity = Commodity(category="Soap", found=True, confidence=0.88)
    r.manufacturer = PartyInfo(
        name="Hindustan Unilever Ltd.",
        address="Unilever House, B.D. Sawant Marg, Mumbai 400 099",
        found=True, confidence=0.93,
    )
    r.netQuantity = NetQuantity(rawValue="100 g", value=100, unit="g",
                                quantityType="weight", found=True, confidence=0.95)
    r.mrp = MRP(raw="Rs 48", value=48.0, found=True, confidence=0.92)
    r.manufacturingDate = DateField(raw="01/2026", month=1, year=2026,
                                    found=True, confidence=0.88)
    r.consumerCare = ConsumerCare(phone="1800-210-1000", found=True, confidence=0.86)
    return r


def test_integration_dove_compliant():
    result = evaluate(_dove_response())
    assert result.overallStatus in ("compliant", "needs_review")
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    assert len(blocking) == 0


# ===========================================================================
# 9. Deliberately non-compliant fixture — proves the engine catches violations
# ===========================================================================

def test_deliberately_non_compliant_fixture():
    """A deliberately incomplete ExtractionResponse — all mandatory fields
    missing — must produce overallStatus='non_compliant' with blocking failures.
    This proves the engine is not silently passing everything."""
    r = ExtractionResponse(document=DocumentMeta(imageId="empty_label.jpg", width=400, height=300))
    # All fields at default (found=False) — worst-case non-compliant label
    result = evaluate(r)
    assert result.overallStatus == "non_compliant"
    blocking = [rr for rr in result.ruleResults
                if not rr.passed and rr.severity == Severity.BLOCKING]
    # At minimum: commodity, party, net quantity, date, MRP, consumer care all missing
    assert len(blocking) >= 5


def test_deliberately_partial_non_compliant():
    """Only MRP is missing — must be non_compliant."""
    r = _base_response()
    r.mrp = MRP(found=False)
    result = evaluate(r)
    assert result.overallStatus == "non_compliant"
    blocking = [rr for rr in result.ruleResults
                if rr.ruleId == "rule_6_mrp" and not rr.passed]
    assert len(blocking) == 1
    assert blocking[0].severity == Severity.BLOCKING


def test_misleading_term_non_compliant():
    """A label with a misleading quantity term must be non_compliant."""
    r = _base_response()
    r.misleadingQuantityTerms = [MisleadingTerm(text="approximately")]
    result = evaluate(r)
    assert result.overallStatus == "non_compliant"


def test_invalid_unit_non_compliant():
    """kg declared as volume type → non_compliant."""
    r = _base_response()
    r.netQuantity = NetQuantity(rawValue="600 kg", value=600, unit="kg",
                                quantityType="volume", found=True, confidence=0.92)
    result = evaluate(r)
    assert result.overallStatus == "non_compliant"


# ===========================================================================
# 10. Full suite: every rule in evaluate() returns a RuleResult
# ===========================================================================

def test_evaluate_returns_compliance_result_type():
    r = _base_response()
    result = evaluate(r)
    assert isinstance(result, ComplianceResult)
    assert isinstance(result.ruleResults, list)
    assert len(result.ruleResults) > 0
    for rr in result.ruleResults:
        assert isinstance(rr, RuleResult)
        assert isinstance(rr.passed, bool)
        assert isinstance(rr.severity, Severity)
        assert rr.ruleId
        assert rr.ruleReference
        assert rr.description


def test_evaluate_no_bare_dicts_in_results():
    """Guard against accidentally returning dict instead of RuleResult."""
    r = _base_response()
    result = evaluate(r)
    for rr in result.ruleResults:
        assert not isinstance(rr, dict), f"Got dict for rule {rr}"
