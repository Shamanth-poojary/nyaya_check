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
    ruleId: str = Field(
        ...,
        description="Stable snake_case identifier for the statutory rule",
        examples=["rule_6_mrp_declaration"],
    )
    ruleReference: str = Field(
        ...,
        description="Statutory legal citation from Legal Metrology Rules, 2011",
        examples=["Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 6(1)(e)"],
    )
    description: str = Field(
        ...,
        description="Short human-readable summary of what the rule requires",
        examples=["Maximum Retail Price (MRP) declaration present and legible on package"],
    )
    passed: bool = Field(
        ...,
        description="Whether this statutory requirement is satisfied",
        examples=[True],
    )
    severity: Severity = Field(
        ...,
        description="Severity classification: blocking, warning, info, or needs_review",
        examples=[Severity.BLOCKING],
    )
    evidenceField: Optional[str] = Field(
        default=None,
        description="Underlying extraction field that provided the evidence",
        examples=["mrp"],
    )
    evidenceValue: Optional[str] = Field(
        default=None,
        description="Serialized evidence value inspected during rule evaluation",
        examples=["₹150.00"],
    )
    evidenceConfidence: Optional[float] = Field(
        default=None,
        description="Extraction confidence score for the inspected evidence (0.0 to 1.0)",
        examples=[0.95],
    )
    sourceImage: Optional[str] = Field(
        default=None,
        description="Filename of the packaging photo that contributed this evidence",
        examples=["front_panel.jpg"],
    )
    message: str = Field(
        default="",
        description="Explanatory statement detailing the outcome and findings",
        examples=["MRP declaration found with inclusive of all taxes indication."],
    )


# ---------------------------------------------------------------------------
# Summary counts
# ---------------------------------------------------------------------------

class ComplianceSummary(BaseModel):
    totalChecks: int = Field(default=0, description="Total statutory checks evaluated", examples=[12])
    passed: int = Field(default=0, description="Count of passed checks", examples=[10])
    failed: int = Field(default=0, description="Count of failed checks (blocking or warning)", examples=[0])
    needsReview: int = Field(default=0, description="Count of checks requiring manual human review", examples=[2])
    blocking: int = Field(default=0, description="Count of blocking non-compliant violations", examples=[0])
    warnings: int = Field(default=0, description="Count of warning-level violations", examples=[0])
    infos: int = Field(default=0, description="Count of informational notes", examples=[1])


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------

class ComplianceResult(BaseModel):
    schemaVersion: str = Field(default=COMPLIANCE_SCHEMA_VERSION, description="Rules engine schema version", examples=["3.0"])
    overallStatus: Literal["compliant", "non_compliant", "needs_review"] = Field(
        ...,
        description="Consolidated statutory compliance determination",
        examples=["compliant"],
    )
    ruleResults: List[RuleResult] = Field(
        default_factory=list,
        description="List of individual statutory rule evaluation results",
    )
    summary: ComplianceSummary = Field(
        default_factory=ComplianceSummary,
        description="Aggregate totals of passed, failed, and review-pending checks",
    )


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
