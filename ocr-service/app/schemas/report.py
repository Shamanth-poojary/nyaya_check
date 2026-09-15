"""
app/schemas/report.py — Phase 04 Report Generation schemas.

Defines the final ComplianceReport contract returned by the POST /check
endpoint, combining the underlying ExtractionResponse (Phase 01/02) and the
ComplianceResult (Phase 03) along with a precomputed ProductSummary for quick
display in frontend UI cards.

Schema version: "4.0" (report generation layer).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.compliance import ComplianceResult
from app.schemas.response import ExtractionResponse

REPORT_SCHEMA_VERSION: str = "4.0"


# ---------------------------------------------------------------------------
# Product summary model (at-a-glance fields for UI rendering & reviewers)
# ---------------------------------------------------------------------------

class ProductSummary(BaseModel):
    """Human-friendly summary of key product attributes, computed once at report
    assembly time so frontend and backend consumers don't need to recompute or
    re-extract from nested structures.
    """
    commodityName: Optional[str] = None
    commodityCategory: Optional[str] = None
    manufacturerName: Optional[str] = None
    packerName: Optional[str] = None
    importerName: Optional[str] = None
    netQuantity: Optional[str] = None
    mrp: Optional[str] = None
    manufacturingDate: Optional[str] = None
    packingDate: Optional[str] = None
    expiryDate: Optional[str] = None
    batchNumber: Optional[str] = None
    consumerCareContact: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level ComplianceReport model
# ---------------------------------------------------------------------------

class ComplianceReport(BaseModel):
    """The authoritative end-to-end report combining full extraction evidence,
    rules engine evaluation results, and high-level product summaries.
    """
    schemaVersion: str = REPORT_SCHEMA_VERSION
    reportId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extraction: ExtractionResponse
    compliance: ComplianceResult
    productSummary: ProductSummary


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def build_product_summary(extraction: ExtractionResponse) -> ProductSummary:
    """Extract and format high-level product summary values from an ExtractionResponse.

    Follows the core design principle: only populate fields if they are found;
    never fabricate values.
    """
    # Commodity
    commodity_name = extraction.commodity.name if extraction.commodity.found else None
    commodity_category = extraction.commodity.category if extraction.commodity.found else None

    # Parties
    manufacturer_name = (
        extraction.manufacturer.name if extraction.manufacturer.found and extraction.manufacturer.name else None
    )
    packer_name = (
        extraction.packer.name if extraction.packer.found and extraction.packer.name else None
    )
    importer_name = (
        extraction.importer.name if extraction.importer.found and extraction.importer.name else None
    )

    # Net Quantity: prefer clean "value unit", fallback to rawValue
    net_quantity = None
    if extraction.netQuantity.found:
        nq = extraction.netQuantity
        if nq.value is not None and nq.unit:
            # Format integer nicely without trailing .0 if integer
            val_str = f"{int(nq.value)}" if nq.value == int(nq.value) else f"{nq.value}"
            net_quantity = f"{val_str} {nq.unit}"
        elif nq.rawValue:
            net_quantity = nq.rawValue

    # MRP: prefer currency + formatted price
    mrp_str = None
    if extraction.mrp.found:
        mrp = extraction.mrp
        if mrp.value is not None:
            symbol = "₹" if mrp.currency == "INR" else f"{mrp.currency} "
            mrp_str = f"{symbol}{mrp.value:.2f}" if mrp.value % 1 != 0 else f"{symbol}{int(mrp.value)}"
        elif mrp.raw:
            mrp_str = mrp.raw

    # Dates
    mfg_date = extraction.manufacturingDate.raw if extraction.manufacturingDate.found else None
    packing_date = extraction.packingDate.raw if extraction.packingDate.found else None
    exp_date = extraction.expiryDate.raw if extraction.expiryDate.found else None

    # Batch number
    batch_num = None
    if extraction.batchNumber.found:
        batch_num = extraction.batchNumber.value or extraction.batchNumber.raw

    # Consumer care
    consumer_contact = None
    if extraction.consumerCare.found:
        cc = extraction.consumerCare
        parts = []
        if cc.phone:
            parts.append(f"Phone: {cc.phone}")
        if cc.email:
            parts.append(f"Email: {cc.email}")
        if cc.name and not parts:
            parts.append(cc.name)
        consumer_contact = ", ".join(parts) if parts else (cc.name or None)

    return ProductSummary(
        commodityName=commodity_name,
        commodityCategory=commodity_category,
        manufacturerName=manufacturer_name,
        packerName=packer_name,
        importerName=importer_name,
        netQuantity=net_quantity,
        mrp=mrp_str,
        manufacturingDate=mfg_date,
        packingDate=packing_date,
        expiryDate=exp_date,
        batchNumber=batch_num,
        consumerCareContact=consumer_contact,
    )


def build_compliance_report(
    extraction: ExtractionResponse,
    compliance: ComplianceResult,
    report_id: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> ComplianceReport:
    """Construct a complete ComplianceReport from an ExtractionResponse and a ComplianceResult."""
    summary = build_product_summary(extraction)
    kwargs = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "extraction": extraction,
        "compliance": compliance,
        "productSummary": summary,
    }
    if report_id:
        kwargs["reportId"] = report_id
    if generated_at:
        kwargs["generatedAt"] = generated_at

    return ComplianceReport(**kwargs)
