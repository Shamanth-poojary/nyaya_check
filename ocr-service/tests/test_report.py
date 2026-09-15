"""
tests/test_report.py — Comprehensive tests for Phase 04 Report Generation.

Covers:
  1. ProductSummary extraction unit tests
  2. ComplianceReport model validation unit tests
  3. render_report_markdown() unit tests with hand-crafted fixtures
  4. POST /check endpoint single-image & multi-image integration tests
  5. Format switching tests (?format=markdown, Accept: text/markdown, ?format=pdf)
  6. Error handling tests (corrupt images, non-images, empty upload, too many images)
  7. Real-product pipeline integration tests (real photos + real OCR fixtures)
"""

import io
import time
from datetime import datetime, timezone
from typing import List

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.reporting.markdown_renderer import render_report_markdown
from app.rules.engine import evaluate
from app.schemas.compliance import (
    ComplianceResult,
    ComplianceSummary,
    RuleResult,
    Severity,
)
from app.schemas.report import (
    REPORT_SCHEMA_VERSION,
    ComplianceReport,
    ProductSummary,
    build_compliance_report,
    build_product_summary,
)
from app.schemas.response import (
    MRP,
    BatchNumber,
    BoundingBox,
    Commodity,
    ConsumerCare,
    DateField,
    DocumentMeta,
    ExtractionResponse,
    NetQuantity,
    PartyInfo,
    RawOCRLine,
)

client = TestClient(app)


def _sample_image_bytes(width: int = 120, height: int = 80, color=(255, 255, 255)) -> io.BytesIO:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _sample_jpeg_bytes(width: int = 120, height: int = 80) -> io.BytesIO:
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 1. ProductSummary unit tests
# ---------------------------------------------------------------------------

class TestProductSummary:

    def test_build_product_summary_complete(self):
        r = ExtractionResponse(
            document=DocumentMeta(imageId="test.jpg", width=800, height=1200),
            commodity=Commodity(name="Hana Lemon Drink", category="Beverage", found=True, confidence=0.9),
            manufacturer=PartyInfo(name="ABC Beverages Pvt Ltd", address="Mumbai, India", found=True, confidence=0.95),
            packer=PartyInfo(name="XYZ Packaging Ltd", found=True, confidence=0.88),
            netQuantity=NetQuantity(rawValue="600 ml", value=600.0, unit="ml", found=True, confidence=0.98),
            mrp=MRP(raw="Rs 40", value=40.0, currency="INR", found=True, confidence=0.92),
            manufacturingDate=DateField(raw="26/03/2026", month=3, year=2026, found=True, confidence=0.9),
            expiryDate=DateField(raw="26/09/2026", month=9, year=2026, found=True, confidence=0.9),
            batchNumber=BatchNumber(value="B.NO:12345", found=True, confidence=0.85),
            consumerCare=ConsumerCare(phone="1800-123-456", email="care@example.com", found=True, confidence=0.9),
        )

        summary = build_product_summary(r)
        assert summary.commodityName == "Hana Lemon Drink"
        assert summary.commodityCategory == "Beverage"
        assert summary.manufacturerName == "ABC Beverages Pvt Ltd"
        assert summary.packerName == "XYZ Packaging Ltd"
        assert summary.netQuantity == "600 ml"
        assert summary.mrp == "₹40"
        assert summary.manufacturingDate == "26/03/2026"
        assert summary.expiryDate == "26/09/2026"
        assert summary.batchNumber == "B.NO:12345"
        assert "1800-123-456" in summary.consumerCareContact
        assert "care@example.com" in summary.consumerCareContact

    def test_build_product_summary_empty_when_not_found(self):
        r = ExtractionResponse(
            document=DocumentMeta(imageId="empty.jpg", width=100, height=100)
        )
        summary = build_product_summary(r)
        assert summary.commodityName is None
        assert summary.commodityCategory is None
        assert summary.manufacturerName is None
        assert summary.netQuantity is None
        assert summary.mrp is None
        assert summary.batchNumber is None
        assert summary.consumerCareContact is None

    def test_build_product_summary_float_net_qty_and_mrp(self):
        r = ExtractionResponse(
            document=DocumentMeta(imageId="test.jpg", width=100, height=100),
            netQuantity=NetQuantity(value=1.5, unit="kg", found=True, confidence=0.9),
            mrp=MRP(value=99.50, currency="INR", found=True, confidence=0.95),
        )
        summary = build_product_summary(r)
        assert summary.netQuantity == "1.5 kg"
        assert summary.mrp == "₹99.50"


# ---------------------------------------------------------------------------
# 2. Markdown Renderer Unit Tests
# ---------------------------------------------------------------------------

class TestMarkdownRenderer:

    @pytest.fixture
    def mock_report(self) -> ComplianceReport:
        extraction = ExtractionResponse(
            document=DocumentMeta(imageId="dove_front.jpg", width=600, height=800),
            sourceDocuments=[
                DocumentMeta(imageId="dove_front.jpg", width=600, height=800),
                DocumentMeta(imageId="dove_back.jpg", width=600, height=800),
            ],
            commodity=Commodity(name="Bathing Bar", category="Cosmetics", found=True, confidence=0.92),
            manufacturer=PartyInfo(name="Hindustan Unilever Ltd.", found=True, confidence=0.96),
            netQuantity=NetQuantity(rawValue="100 g", value=100, unit="g", found=True, confidence=0.95),
            mrp=MRP(raw="Rs 65", value=65.0, found=True, confidence=0.94),
            manufacturingDate=DateField(raw="01/2026", month=1, year=2026, found=True, confidence=0.89),
            batchNumber=BatchNumber(value="BN9876", found=True, confidence=0.88),
            consumerCare=ConsumerCare(phone="1800-102-2221", found=True, confidence=0.91),
            rawOCR=[
                RawOCRLine(text="DOVE SOAP", bbox=BoundingBox(xmin=10, ymin=10, xmax=100, ymax=30), confidence=0.98),
                RawOCRLine(text="Net Wt: 100g", bbox=BoundingBox(xmin=10, ymin=40, xmax=120, ymax=60), confidence=0.95),
            ],
        )

        rule_results = [
            RuleResult(
                ruleId="rule_6_commodity_name",
                ruleReference="Legal Metrology Rules, 2011 — Rule 6(1)(a)",
                description="Generic or common name of commodity",
                passed=True,
                severity=Severity.INFO,
                evidenceField="commodity.category",
                evidenceValue="Cosmetics",
                evidenceConfidence=0.92,
                sourceImage="dove_front.jpg",
                message="Commodity identified as Cosmetics",
            ),
            RuleResult(
                ruleId="rule_6_mrp_declaration",
                ruleReference="Legal Metrology Rules, 2011 — Rule 6(1)(e)",
                description="Maximum Retail Price declaration",
                passed=True,
                severity=Severity.INFO,
                evidenceField="mrp",
                evidenceValue="₹65",
                evidenceConfidence=0.94,
                sourceImage="dove_back.jpg",
                message="Valid MRP declaration present",
            ),
            RuleResult(
                ruleId="rule_10_quantity_clearance",
                ruleReference="Legal Metrology Rules, 2011 — Rule 10(1)",
                description="Clearance surrounding net quantity declaration",
                passed=False,
                severity=Severity.WARNING,
                evidenceField="visual.quantityClearance",
                evidenceValue="aboveRatio=0.15",
                evidenceConfidence=0.85,
                sourceImage="dove_front.jpg",
                message="Clearance space above net quantity is tighter than standard recommendation",
            ),
        ]

        compliance = ComplianceResult(
            overallStatus="compliant",
            ruleResults=rule_results,
            summary=ComplianceSummary(
                totalChecks=3,
                passed=2,
                failed=1,
                needsReview=0,
                blocking=0,
                warnings=1,
                infos=2,
            ),
        )

        return build_compliance_report(
            extraction=extraction,
            compliance=compliance,
            report_id="rpt-dove-test-uuid",
            generated_at=datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

    def test_render_report_markdown_contains_all_key_data(self, mock_report):
        md = render_report_markdown(mock_report)

        # Header & Metadata
        assert "Legal Metrology Compliance Report" in md
        assert "rpt-dove-test-uuid" in md
        assert f"Report `v{REPORT_SCHEMA_VERSION}`" in md

        # Executive Summary & Overall Status
        assert "PASS — COMPLIANT" in md
        assert "| Total Checks | 3 |" in md
        assert "| Passed | 2 |" in md
        assert "| Warnings | 1 |" in md

        # Product Summary Card
        assert "Bathing Bar (Cosmetics)" in md
        assert "Hindustan Unilever Ltd." in md
        assert "100 g" in md
        assert "₹65" in md
        assert "Mfg: 01/2026" in md
        assert "BN9876" in md
        assert "1800-102-2221" in md

        # Rule Results Table
        assert "Rule 6(1)(a)" in md
        assert "Rule 6(1)(e)" in md
        assert "Rule 10(1)" in md
        assert "WARNING" in md
        assert "dove_front.jpg" in md

        # Traceability
        assert "dove_front.jpg" in md
        assert "dove_back.jpg" in md
        assert "Total Raw OCR Detections:** 2" in md

    def test_render_report_markdown_needs_review_and_uncertainties(self):
        extraction = ExtractionResponse(
            document=DocumentMeta(imageId="mystery.jpg", width=500, height=500),
            uncertainFields=["OCR confidence low on MRP", "Multiple possible manufacturing dates"],
        )
        compliance = ComplianceResult(
            overallStatus="needs_review",
            ruleResults=[
                RuleResult(
                    ruleId="rule_6_mrp_declaration",
                    ruleReference="Rule 6(1)(e)",
                    description="MRP declaration",
                    passed=False,
                    severity=Severity.NEEDS_REVIEW,
                    message="MRP OCR confidence below threshold; manual verification required.",
                )
            ],
            summary=ComplianceSummary(totalChecks=1, needsReview=1),
        )
        report = build_compliance_report(extraction, compliance)
        md = render_report_markdown(report)

        assert "ACTION REQUIRED — NEEDS REVIEW" in md
        assert "NEEDS REVIEW" in md
        assert "Pipeline Warnings & Uncertainties" in md
        assert "OCR confidence low on MRP" in md


# ---------------------------------------------------------------------------
# 3. POST /check Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestCheckEndpoint:

    def test_check_single_image_json(self):
        buf = _sample_image_bytes(100, 80)
        resp = client.post(
            "/check",
            files={"image": ("single.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()

        # Schema & Identifiers
        assert data["schemaVersion"] == REPORT_SCHEMA_VERSION
        assert "reportId" in data and len(data["reportId"]) > 0
        assert "generatedAt" in data

        # Components present
        assert "extraction" in data
        assert "compliance" in data
        assert "productSummary" in data

        # Nested details
        assert data["extraction"]["document"]["imageId"] == "single.png"
        assert "overallStatus" in data["compliance"]
        assert "ruleResults" in data["compliance"]
        assert "totalChecks" in data["compliance"]["summary"]

    def test_check_multi_image_json(self):
        buf1 = _sample_image_bytes(100, 80)
        buf2 = _sample_image_bytes(120, 90)
        resp = client.post(
            "/check",
            files=[
                ("images", ("front.png", buf1, "image/png")),
                ("images", ("back.png", buf2, "image/png")),
            ],
        )
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["extraction"]["sourceDocuments"]) == 2
        docs = {d["imageId"] for d in data["extraction"]["sourceDocuments"]}
        assert docs == {"front.png", "back.png"}
        assert data["compliance"]["overallStatus"] in ("compliant", "non_compliant", "needs_review")

    def test_check_format_markdown_query_param(self):
        buf = _sample_image_bytes(100, 80)
        resp = client.post(
            "/check?format=markdown",
            files={"image": ("single.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        body = resp.text
        assert "# Legal Metrology Compliance Report" in body
        assert "## Executive Summary" in body
        assert "## Product Summary" in body
        assert "## Rule Evaluation Details" in body

    def test_check_accept_header_markdown(self):
        buf = _sample_image_bytes(100, 80)
        resp = client.post(
            "/check",
            files={"image": ("single.png", buf, "image/png")},
            headers={"Accept": "text/markdown"},
        )
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert "# Legal Metrology Compliance Report" in resp.text

    def test_check_format_pdf_returns_informative_400(self):
        buf = _sample_image_bytes(100, 80)
        resp = client.post(
            "/check?format=pdf",
            files={"image": ("single.png", buf, "image/png")},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "PDF_DECISION.md" in data["detail"]
        assert "deferred" in data["detail"].lower()

    def test_check_v1_alias_works(self):
        buf = _sample_image_bytes(100, 80)
        resp = client.post(
            "/v1/check",
            files={"image": ("single.png", buf, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["schemaVersion"] == REPORT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# 4. Error Handling Tests
# ---------------------------------------------------------------------------

class TestCheckErrorHandling:

    def test_rejects_empty_upload(self):
        resp = client.post("/check")
        assert resp.status_code in (400, 422)

    def test_rejects_non_image_file(self):
        resp = client.post(
            "/check",
            files={"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert resp.status_code == 400
        assert "Unsupported content type" in resp.json()["detail"]

    def test_rejects_corrupted_image_bytes(self):
        resp = client.post(
            "/check",
            files={"image": ("corrupted.png", io.BytesIO(b"\x89PNG\r\n\x1a\nCorruptBytesHere"), "image/png")},
        )
        assert resp.status_code == 400
        assert "not a valid image" in resp.json()["detail"].lower()

    def test_rejects_too_many_images(self):
        files = [
            ("images", (f"img_{i}.png", _sample_image_bytes(30, 30), "image/png"))
            for i in range(11)
        ]
        resp = client.post("/check", files=files)
        assert resp.status_code == 400
        assert "Too many images" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 5. Full Real-Product Pipeline Integration Tests
# ---------------------------------------------------------------------------

class TestRealProductPipeline:

    def test_real_image_end_to_end(self):
        """Run POST /check with an actual image file from test_images."""
        import os

        real_img_path = os.path.join(
            "test_images", "clean", "ChatGPT Image Sep 15, 2026, 09_00_10 AM.png"
        )
        if not os.path.exists(real_img_path):
            pytest.skip(f"Test image not found at {real_img_path}")

        start_time = time.time()
        with open(real_img_path, "rb") as f:
            resp = client.post(
                "/check",
                files={"image": ("real_clean_product.png", f.read(), "image/png")},
            )
        elapsed = time.time() - start_time

        assert resp.status_code == 200
        data = resp.json()
        assert data["schemaVersion"] == REPORT_SCHEMA_VERSION
        assert data["reportId"] is not None
        assert "compliance" in data
        assert "extraction" in data
        assert "productSummary" in data
        assert data["compliance"]["overallStatus"] in ("compliant", "non_compliant", "needs_review")
        # Validate that latency was reasonable (< 15 seconds for single OCR pass)
        print(f"\n[Real Image End-to-End Latency]: {elapsed:.2f}s")
        assert elapsed < 15.0

    @pytest.mark.parametrize(
        "product_name,category,party,qty,mrp_val",
        [
            ("Everest Turmeric", "Spices", "Everest Food Products Pvt. Ltd.", "100 g", 35.0),
            ("Haldiram's Bhujia", "Snacks", "Haldiram Snacks Pvt. Ltd.", "200 g", 55.0),
            ("Bisleri Water", "Packaged Drinking Water", "Bisleri International Pvt. Ltd.", "1000 ml", 20.0),
            ("Tata Tea Gold", "Tea", "Tata Consumer Products Ltd.", "500 g", 230.0),
            ("Aashirvaad Atta", "Flour", "ITC Limited", "5 kg", 280.0),
            ("Nandini Milk", "Dairy", "Karnataka Co-operative Milk Producers' Federation Ltd.", "1000 ml", 50.0),
        ],
    )
    def test_multi_product_report_generation(self, product_name, category, party, qty, mrp_val):
        """Verify report generation across multi-category product fixtures."""
        r = ExtractionResponse(
            document=DocumentMeta(imageId=f"{product_name.lower().replace(' ', '_')}.jpg", width=600, height=800),
            commodity=Commodity(name=product_name, category=category, found=True, confidence=0.9),
            manufacturer=PartyInfo(name=party, address="Sample Address", found=True, confidence=0.92),
            netQuantity=NetQuantity(rawValue=qty, value=float(qty.split()[0]), unit=qty.split()[1], found=True, confidence=0.95),
            mrp=MRP(raw=f"Rs {mrp_val}", value=mrp_val, currency="INR", found=True, confidence=0.9),
            packingDate=DateField(raw="06/2026", month=6, year=2026, found=True, confidence=0.9),
            consumerCare=ConsumerCare(phone="1800-111-222", found=True, confidence=0.88),
        )

        comp = evaluate(r)
        report = build_compliance_report(extraction=r, compliance=comp)

        # Validate summary fields
        assert report.productSummary.commodityName == product_name
        assert report.productSummary.commodityCategory == category
        assert report.productSummary.manufacturerName == party
        assert report.productSummary.netQuantity == qty

        # Validate markdown generation for every product
        md = render_report_markdown(report)
        assert product_name in md
        assert party in md
        assert qty in md
        assert report.reportId in md
