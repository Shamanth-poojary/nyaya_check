"""
app/routes/check.py — Phase 04 End-to-End Compliance Check Endpoint.

Exposes:
  POST /check (and alias /v1/check)

Runs the entire pipeline from end to end:
  1. Image validation & multi-image upload handling
  2. OCR + normalization + field classification
  3. Visual analysis (font ratios, contrast, spacing, PDP)
  4. Rules engine compliance evaluation
  5. Assembly of the final ComplianceReport
  6. Multi-format response negotiation (JSON default, Markdown human-summary)
"""

from __future__ import annotations

import logging
from typing import List, Optional, Union

from fastapi import APIRouter, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse

from app.classification.merge import merge_extraction_results
from app.pipeline import process_single_image
from app.reporting.markdown_renderer import render_report_markdown
from app.routes.ocr import MAX_IMAGES_PER_REQUEST
from app.rules.engine import evaluate
from app.schemas.report import ComplianceReport, build_compliance_report
from app.visual.layout import identify_principal_display_panel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/check",
    response_model=ComplianceReport,
    responses={
        200: {
            "content": {
                "application/json": {},
                "text/markdown": {},
            },
            "description": "Full end-to-end Legal Metrology compliance report.",
        }
    },
)
@router.post("/v1/check", response_model=ComplianceReport, include_in_schema=False)
async def check(
    request: Request,
    images: Optional[List[UploadFile]] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
    preprocess_enabled: bool = False,
    format: Optional[str] = Query(
        default=None,
        description="Desired output format: 'json' (default) or 'markdown'. PDF is deferred (see PDF_DECISION.md).",
    ),
    accept: Optional[str] = Header(default=None),
) -> Union[ComplianceReport, PlainTextResponse]:
    """Execute the full Legal Metrology compliance check pipeline on one or more product photos.

    Accepts:
      - Multi-image uploads via `images` (List[UploadFile])
      - Single-image uploads via `image` or single item in `images`

    Formats:
      - `format=json` (default): returns structured `ComplianceReport` Pydantic model
      - `format=markdown` or `Accept: text/markdown`: returns human-readable Markdown summary
      - `format=pdf`: returns HTTP 400 explaining PDF deferral (see PDF_DECISION.md)
    """
    # 1. Format parameter validation
    fmt = (format or "").lower().strip()
    if fmt == "pdf":
        raise HTTPException(
            status_code=400,
            detail=(
                "PDF export is currently deferred per system architecture decision. "
                "Please consult PDF_DECISION.md or request format=json / format=markdown."
            ),
        )

    # 2. Collect uploaded images
    file_list: List[UploadFile] = []
    if images:
        file_list.extend(images)
    if image:
        file_list.append(image)

    if not file_list:
        raise HTTPException(
            status_code=400,
            detail="No image uploaded. Please supply at least one image via 'image' or 'images'.",
        )

    if len(file_list) > MAX_IMAGES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Too many images ({len(file_list)}); max {MAX_IMAGES_PER_REQUEST} per request.",
        )

    # 3. Execute extraction pipeline per image
    single_results = [
        await process_single_image(img, preprocess_enabled=preprocess_enabled)
        for img in file_list
    ]

    # 4. Consolidate multi-image results
    if len(single_results) == 1:
        extraction = single_results[0]
        if not extraction.sourceDocuments:
            extraction.sourceDocuments = [extraction.document]
    else:
        extraction = merge_extraction_results(single_results)
        # For multi-image: attach visual evidence from the likely PDP photo
        pdp = identify_principal_display_panel(extraction)
        extraction.visual.principalDisplayPanel = pdp
        if pdp and pdp.likelySourceImage:
            matching = next(
                (r for r in single_results if r.document.imageId == pdp.likelySourceImage),
                None,
            )
            if matching and matching.visual:
                extraction.visual.relativeFontSizes = matching.visual.relativeFontSizes
                extraction.visual.netQuantityMedianRatio = matching.visual.netQuantityMedianRatio
                extraction.visual.contrast = matching.visual.contrast
                extraction.visual.readability = matching.visual.readability
                extraction.visual.quantityClearance = matching.visual.quantityClearance

    # 5. Run rules engine
    compliance = evaluate(extraction)

    # 6. Assemble ComplianceReport
    report = build_compliance_report(extraction=extraction, compliance=compliance)

    # 7. Content negotiation / response formatting
    wants_markdown = fmt in ("markdown", "md") or (
        not fmt and accept and "text/markdown" in accept
    )
    if wants_markdown:
        md_text = render_report_markdown(report)
        return PlainTextResponse(content=md_text, media_type="text/markdown")

    return report
