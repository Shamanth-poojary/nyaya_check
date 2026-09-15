"""
app/schemas/compliance.py — Phase 03 Rules Engine output schema.

Defines the structured compliance result produced by the rules engine after
evaluating a completed ExtractionResponse.  This schema is intentionally
separate from app/schemas/response.py to keep the compliance concerns cleanly
decoupled from the extraction concerns.

Overall-status decision tree (pure function compute_overall_status):
    1. Any RuleResult with severity=BLOCKING and passed=False  → "non_compliant"
    2. No blocking failures, but any severity=NEEDS_REVIEW      → "needs_review"
    3. Otherwise                                                → "compliant"

Schema version: "3.0" (rules engine layer; extraction layer is "2.0").
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


COMPLIANCE_SCHEMA_VERSION: str = "3.0"

# ---------------------------------------------------------------------------
# Confidence threshold
# ---------------------------------------------------------------------------
# Fields whose confidence is below this value (or that appear in
# uncertainFields) cause the rules engine to downgrade what would otherwise
# be a BLOCKING failure or a confident pass to NEEDS_REVIEW.
# Rationale: a compliance tool that confidently asserts a violation (or a
# pass) based on shaky OCR is worse than one that honestly says
# "can't tell — check manually."
LOW_CONFIDENCE_THRESHOLD: float = 0.6


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    BLOCKING = "blocking"
    # Clear, confident rule violation with high-confidence evidence.

    WARNING = "warning"
    # Likely issue but based on low-confidence or heuristic evidence
    # (e.g. visual analysis readability flags).

    INFO = "info"
    # Informational, not a violation
    # (e.g. "packer not applicable — only manufacturer role present").

    NEEDS_REVIEW = "needs_review"
    # Rules engine cannot determine pass/fail from available evidence
    # (low OCR confidence, field in uncertainFields, ambiguous data).


# ---------------------------------------------------------------------------
# Rule result
# ---------------------------------------------------------------------------

class RuleResult(BaseModel):
    ruleId: str
    # Stable snake_case identifier, e.g. "rule_6_manufacturer_declaration".

    ruleReference: str
    # Human-readable legal citation,
    # e.g. "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)".

    description: str
    # Short description of what was checked, e.g. "Manufacturer name and
    # address present on label".

    passed: bool
    # True if the check passed (including NEEDS_REVIEW — that field is still
    # considered "not a confirmed failure").

    severity: Severity
    # Severity of this result.  BLOCKING/WARNING only make sense when
    # passed=False.  INFO is used for inapplicable checks.

    evidenceField: Optional[str] = None
    # Which ExtractionResponse field the evidence came from,
    # e.g. "manufacturer", "netQuantity.unit".

    evidenceValue: Optional[str] = None
    # The actual value inspected, serialised as a string for readability.

    evidenceConfidence: Optional[float] = None
    # Confidence of the extracted evidence (from the source field).

    sourceImage: Optional[str] = None
    # Which uploaded photo contributed the evidence.

    message: str = ""
    # Specific human-readable explanation of the result.


# ---------------------------------------------------------------------------
# Summary counts
# ---------------------------------------------------------------------------

class ComplianceSummary(BaseModel):
    totalChecks: int = 0
    passed: int = 0
    failed: int = 0
    needsReview: int = 0
    blocking: int = 0    # count of BLOCKING failures
    warnings: int = 0    # count of WARNING failures
    infos: int = 0       # count of INFO results


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------

class ComplianceResult(BaseModel):
    schemaVersion: str = COMPLIANCE_SCHEMA_VERSION
    overallStatus: Literal["compliant", "non_compliant", "needs_review"]
    ruleResults: List[RuleResult] = Field(default_factory=list)
    summary: ComplianceSummary = Field(default_factory=ComplianceSummary)


# ---------------------------------------------------------------------------
# Pure helper: compute overall status
# ---------------------------------------------------------------------------

def compute_overall_status(
    results: List[RuleResult],
) -> Literal["compliant", "non_compliant", "needs_review"]:
    """Determine the overall compliance status from a list of rule results.

    Decision tree (documented in 03_rules_engine.md):
        1. Any BLOCKING failure (passed=False, severity=BLOCKING) → "non_compliant"
        2. No blocking failures but any NEEDS_REVIEW present      → "needs_review"
        3. Otherwise                                               → "compliant"

    This is a pure function with no side-effects, making it trivially
    testable in isolation.
    """
    has_blocking_failure = any(
        not r.passed and r.severity == Severity.BLOCKING for r in results
    )
    if has_blocking_failure:
        return "non_compliant"

    has_needs_review = any(r.severity == Severity.NEEDS_REVIEW for r in results)
    if has_needs_review:
        return "needs_review"

    return "compliant"


def build_summary(results: List[RuleResult]) -> ComplianceSummary:
    """Aggregate counts from a list of RuleResult objects."""
    summary = ComplianceSummary(totalChecks=len(results))
    for r in results:
        if r.severity == Severity.NEEDS_REVIEW:
            summary.needsReview += 1
        elif r.passed:
            summary.passed += 1
        else:
            summary.failed += 1
            if r.severity == Severity.BLOCKING:
                summary.blocking += 1
            elif r.severity == Severity.WARNING:
                summary.warnings += 1
        if r.severity == Severity.INFO:
            summary.infos += 1
    return summary
