import os
import glob
import asyncio
from fastapi import UploadFile
from app.pipeline import process_single_image
from app.rules.engine import evaluate
from app.schemas.report import build_compliance_report

async def main():
    test_dir = os.path.join(os.path.dirname(__file__), "test_images")
    image_paths = sorted(glob.glob(os.path.join(test_dir, "*", "*.png")))
    print(f"============================================================")
    print(f"Verifying Brand & Commodity Identification on {len(image_paths)} Test Images")
    print(f"============================================================\n")

    for path in image_paths:
        folder = os.path.basename(os.path.dirname(path))
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            content = f.read()
        
        from starlette.datastructures import Headers
        import io
        upload_file = UploadFile(
            filename=filename,
            file=io.BytesIO(content),
            headers=Headers({"content-type": "image/png"})
        )

        extraction = await process_single_image(upload_file, preprocess_enabled=False)
        compliance = evaluate(extraction)
        report = build_compliance_report(extraction, compliance)

        rule6a = next((r for r in compliance.ruleResults if r.ruleId == "rule_6_commodity_identity"), None)
        rule6a_status = "PASS" if (rule6a and rule6a.passed and rule6a.severity.value != "needs_review") else ("REVIEW" if (rule6a and rule6a.severity.value == "needs_review") else "FAIL")

        print(f"[{folder}] {filename}")
        print(f"   Brand / Commodity Name: '{report.productSummary.commodityName}'")
        print(f"   Commodity Category:     '{report.productSummary.commodityCategory}'")
        print(f"   Rule 6(1)(a) Status:    [{rule6a_status}] (Severity: {rule6a.severity.value if rule6a else 'None'})")
        print(f"   Evidence:               {rule6a.evidenceValue if rule6a else 'None'}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
