"""
app/reporting/markdown_renderer.py — Phase 04 Markdown summary renderer.

Renders a structured, publication-quality Markdown report from a ComplianceReport,
providing immediate, human-readable visibility into product identity, overall
compliance status, detailed rule results, and underlying evidence.
"""

from __future__ import annotations

from app.schemas.compliance import Severity
from app.schemas.report import ComplianceReport


def _escape_cell(text: str) -> str:
    """Escape pipe characters and line breaks for Markdown table cells."""
    if not text:
        return ""
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_report_markdown(report: ComplianceReport) -> str:
    """Produce a clean, formatted Markdown report from a ComplianceReport.

    Sections:
      1. Header & Metadata (ID, timestamps, schema versions)
      2. Executive Summary & Overall Status
      3. Product Summary (identity card)
      4. Rule Evaluation Results Table
      5. Traceability & Evidence (source images, uncertain fields)
    """
    lines = []

    # 1. Header
    lines.append("# Legal Metrology Compliance Report")
    lines.append("")
    lines.append(f"**Report ID:** `{report.reportId}`  ")
    lines.append(f"**Generated At:** `{report.generatedAt.isoformat()}`  ")
    lines.append(
        f"**Schemas:** Report `v{report.schemaVersion}` | "
        f"Compliance `v{report.compliance.schemaVersion}` | "
        f"Extraction `v{report.extraction.schemaVersion}`"
    )
    lines.append("")

    # 2. Executive Summary
    status_label = {
        "compliant": "PASS — COMPLIANT",
        "non_compliant": "FAIL — NON-COMPLIANT",
        "needs_review": "ACTION REQUIRED — NEEDS REVIEW",
    }.get(report.compliance.overallStatus, report.compliance.overallStatus.upper())

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"### Overall Status: **{status_label}**")
    lines.append("")

    sumry = report.compliance.summary
    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| Total Checks | {sumry.totalChecks} |")
    lines.append(f"| Passed | {sumry.passed} |")
    lines.append(f"| Failed | {sumry.failed} |")
    lines.append(f"| Needs Review | {sumry.needsReview} |")
    lines.append(f"| Blocking Violations | {sumry.blocking} |")
    lines.append(f"| Warnings | {sumry.warnings} |")
    lines.append(f"| Informational | {sumry.infos} |")
    lines.append("")

    # 3. Product Summary
    ps = report.productSummary
    lines.append("## Product Summary")
    lines.append("")
    lines.append("| Attribute | Extracted Value |")
    lines.append("|---|---|")
    
    comm = ps.commodityName or "—"
    cat = f" ({ps.commodityCategory})" if ps.commodityCategory else ""
    lines.append(f"| Commodity | {_escape_cell(comm + cat)} |")
    lines.append(f"| Manufacturer | {_escape_cell(ps.manufacturerName or '—')} |")
    if ps.packerName:
        lines.append(f"| Packer | {_escape_cell(ps.packerName)} |")
    if ps.importerName:
        lines.append(f"| Importer | {_escape_cell(ps.importerName)} |")
    lines.append(f"| Net Quantity | {_escape_cell(ps.netQuantity or '—')} |")
    lines.append(f"| MRP | {_escape_cell(ps.mrp or '—')} |")
    
    dates_part = []
    if ps.manufacturingDate:
        dates_part.append(f"Mfg: {ps.manufacturingDate}")
    if ps.packingDate:
        dates_part.append(f"Pkg: {ps.packingDate}")
    if ps.expiryDate:
        dates_part.append(f"Exp: {ps.expiryDate}")
    dates_str = " | ".join(dates_part) if dates_part else "—"
    lines.append(f"| Dates | {_escape_cell(dates_str)} |")
    lines.append(f"| Batch Number | {_escape_cell(ps.batchNumber or '—')} |")
    lines.append(f"| Consumer Care | {_escape_cell(ps.consumerCareContact or '—')} |")
    lines.append("")

    # 4. Detailed Rule Results
    lines.append("## Rule Evaluation Details")
    lines.append("")
    lines.append(
        "| Rule Citation | Description | Result | Severity | Evidence | Explanation |"
    )
    lines.append("|---|---|---|---|---|---|")

    for rule in report.compliance.ruleResults:
        ref = _escape_cell(rule.ruleReference)
        desc = _escape_cell(rule.description)
        
        if rule.severity == Severity.NEEDS_REVIEW:
            res_str = "NEEDS REVIEW"
        elif rule.passed:
            res_str = "PASS"
        else:
            res_str = "FAIL"

        sev_str = rule.severity.value.upper()

        ev_parts = []
        if rule.evidenceField:
            ev_parts.append(f"field: {rule.evidenceField}")
        if rule.evidenceValue:
            ev_parts.append(f"val: {rule.evidenceValue}")
        if rule.evidenceConfidence is not None:
            ev_parts.append(f"conf: {rule.evidenceConfidence:.2f}")
        if rule.sourceImage:
            ev_parts.append(f"src: {rule.sourceImage}")
        ev_str = _escape_cell("; ".join(ev_parts) if ev_parts else "—")

        msg = _escape_cell(rule.message)

        lines.append(f"| {ref} | {desc} | {res_str} | {sev_str} | {ev_str} | {msg} |")

    lines.append("")

    # 5. Traceability & Evidence
    lines.append("## Traceability & Evidence")
    lines.append("")
    docs = (
        report.extraction.sourceDocuments
        if report.extraction.sourceDocuments
        else [report.extraction.document]
    )
    lines.append(f"**Submitted Images ({len(docs)}):**")
    for doc in docs:
        lines.append(f"- `{doc.imageId}` ({doc.width}x{doc.height} px)")
    lines.append("")
    lines.append(f"**Total Raw OCR Detections:** {len(report.extraction.rawOCR)}")
    lines.append("")

    if report.extraction.uncertainFields:
        lines.append("### Pipeline Warnings & Uncertainties")
        for u in report.extraction.uncertainFields:
            lines.append(f"- ⚠️ {_escape_cell(u)}")
        lines.append("")

    return "\n".join(lines)
