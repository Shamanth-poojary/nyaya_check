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
    commodityName: Optional[str] = Field(
        default=None,
        description="Declared commercial commodity name",
        examples=["Turmeric Powder"],
    )
    commodityCategory: Optional[str] = Field(
        default=None,
        description="Matched schedule commodity category",
        examples=["spices_and_condiments"],
    )
    manufacturerName: Optional[str] = Field(
        default=None,
        description="Name of declared manufacturer",
        examples=["Everest Food Products Pvt. Ltd."],
    )
    packerName: Optional[str] = Field(
        default=None,
        description="Name of declared packer if distinct from manufacturer",
        examples=[None],
    )
    importerName: Optional[str] = Field(
        default=None,
        description="Name of declared importer for imported commodities",
        examples=[None],
    )
    netQuantity: Optional[str] = Field(
        default=None,
        description="Formatted declared net quantity string",
        examples=["100 g"],
    )
    mrp: Optional[str] = Field(
        default=None,
        description="Formatted declared retail price with currency",
        examples=["₹35.00"],
    )
    manufacturingDate: Optional[str] = Field(
        default=None,
        description="Raw or formatted date of manufacture",
        examples=["03/2024"],
    )
    packingDate: Optional[str] = Field(
        default=None,
        description="Raw or formatted date of packaging",
        examples=[None],
    )
    expiryDate: Optional[str] = Field(
        default=None,
        description="Raw or formatted date of expiry / best before",
        examples=["03/2025"],
    )
    batchNumber: Optional[str] = Field(
        default=None,
        description="Declared batch, lot, or identification code",
        examples=["B.NO. 24A01"],
    )
    consumerCareContact: Optional[str] = Field(
        default=None,
        description="Consumer grievance contact details (phone, email, or address)",
        examples=["Phone: 1800-22-2244, Email: customercare@everestspices.com"],
    )


# ---------------------------------------------------------------------------
# Top-level ComplianceReport model
# ---------------------------------------------------------------------------

class ComplianceReport(BaseModel):
    """The authoritative end-to-end report combining full extraction evidence,
    rules engine evaluation results, and high-level product summaries.
    """
    schemaVersion: str = Field(
        default=REPORT_SCHEMA_VERSION,
        description="Compliance report schema version",
        examples=["4.0"],
    )
    reportId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique identifier for this evaluation report",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    generatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the report was compiled (ISO 8601 UTC)",
        examples=["2026-09-16T07:30:00Z"],
    )
    extraction: ExtractionResponse = Field(
        ...,
        description="Consolidated structured extraction evidence from all submitted photos",
    )
    compliance: ComplianceResult = Field(
        ...,
        description="Statutory legal metrology compliance evaluation results",
    )
    productSummary: ProductSummary = Field(
        ...,
        description="At-a-glance product declarations synthesized for UI presentation",
    )


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
