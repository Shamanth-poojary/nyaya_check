"""
app/rules/engine.py — Rules engine orchestrator.

Public API:
    evaluate(response: ExtractionResponse) -> ComplianceResult

This is the only entry-point the rest of the application (routes, tests)
should call.  It delegates to the individual rule modules, assembles the
final ComplianceResult, and applies the overall-status decision tree.

ARCHITECTURAL RULE: this module imports ONLY from:
  - app.schemas.response   (ExtractionResponse)
  - app.schemas.compliance (ComplianceResult, compute_overall_status, build_summary)
  - app.rules.*            (the individual rule modules)
  NO imports from app.ocr, app.preprocessing, or app.classification.
"""

from __future__ import annotations

from app.schemas.compliance import (
    ComplianceResult,
    build_summary,
    compute_overall_status,
)
from app.schemas.response import ExtractionResponse
from app.rules.rule_6_mandatory import evaluate_rule_6
from app.rules.rules_7_10_visual import evaluate_rules_7_10
from app.rules.rules_11_17_quantity import evaluate_rules_11_17


def evaluate(response: ExtractionResponse) -> ComplianceResult:
    """Evaluate a completed ExtractionResponse against Legal Metrology
    (Packaged Commodities) Rules, 2011 and return a structured ComplianceResult.

    This is a pure function of ExtractionResponse — it never touches images,
    never calls OCR, and never imports from app.ocr / app.preprocessing /
    app.classification.

    Rule evaluation order:
      1. Rule 6  — mandatory declaration presence
      2. Rules 7–10 — visual/spatial legibility (WARNING/NEEDS_REVIEW only)
      3. Rules 11–17 — quantity, unit, and misleading-term checks
    """
    all_results = []
    all_results.extend(evaluate_rule_6(response))
    all_results.extend(evaluate_rules_7_10(response))
    all_results.extend(evaluate_rules_11_17(response))

    overall_status = compute_overall_status(all_results)
    summary = build_summary(all_results)

    return ComplianceResult(
        overallStatus=overall_status,
        ruleResults=all_results,
        summary=summary,
    )
