"""
Real-image integration test script for Phase 02 Visual Analysis.

Runs the full pipeline (OCR → classify → visual analysis) against all
6 test images and prints a detailed report of the visual evidence.
Also identifies any bugs/crashes.

Run with:
  venv\Scripts\python.exe scratch\test_real_images.py
"""

import io
import json
import sys
import os
import traceback
from pathlib import Path

# Force stdout to UTF-8 so the rupee symbol doesn't crash on Windows CP1252 console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import cv2
import numpy as np
from PIL import Image

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.classification.fields import classify_fields
from app.ocr.normalize import merge_split_lines
from app.ocr.paddle import run_ocr
from app.preprocessing.resize import resize_image
from app.schemas.response import BoundingBox, ExtractionResponse, RawOCRLine, empty_response
from app.visual.pipeline import run_visual_analysis

TEST_IMAGES_DIR = Path(__file__).parent.parent / "test_images"

IMAGE_PATHS = {
    "clean (Tetley Green Tea)":       TEST_IMAGES_DIR / "clean"           / "ChatGPT Image Sep 15, 2026, 09_00_10 AM.png",
    "low_contrast (Amul Butter)":     TEST_IMAGES_DIR / "low_contrast"    / "ChatGPT Image Sep 15, 2026, 09_21_44 AM.png",
    "busy_background (Parle-G)":      TEST_IMAGES_DIR / "busy_background" / "ChatGPT Image Sep 15, 2026, 09_17_00 AM.png",
    "glossy (Lays)":                  TEST_IMAGES_DIR / "glossy"          / "ChatGPT Image Sep 15, 2026, 09_18_39 AM.png",
    "mixed (Britannia Marie Gold)":   TEST_IMAGES_DIR / "mixed"           / "ChatGPT Image Sep 15, 2026, 09_20_12 AM.png",
    "rotated (Tata Tea Premium)":     TEST_IMAGES_DIR / "rotated"         / "ChatGPT Image Sep 15, 2026, 09_23_01 AM.png",
}


def process_image(label: str, image_path: Path) -> dict:
    """Run full pipeline on a single real image and return results dict."""
    result = {"label": label, "path": str(image_path), "errors": [], "warnings": []}

    try:
        pil_image = Image.open(image_path).convert("RGB")
        width, height = pil_image.size
        source_name = image_path.name

        response = empty_response(image_id=source_name, width=width, height=height)
        bgr_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Resize for OCR
        ocr_image_bgr, scale = resize_image(bgr_image, max_dimension=1600)
        inverse_scale = 1.0 / scale

        # Save temp file for OCR engine
        import tempfile
        suffix = ".png"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp_path = tmp.name
            cv2.imwrite(tmp_path, ocr_image_bgr)
            lines = run_ocr(tmp_path)
            lines = merge_split_lines(lines)

            response.rawOCR = [
                RawOCRLine(
                    text=line.text,
                    bbox=BoundingBox(
                        xmin=round(line.bbox[0] * inverse_scale),
                        ymin=round(line.bbox[1] * inverse_scale),
                        xmax=round(line.bbox[2] * inverse_scale),
                        ymax=round(line.bbox[3] * inverse_scale),
                    ),
                    confidence=line.confidence,
                    sourceImage=source_name,
                )
                for line in lines
            ]
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Tag source image
        from app.pipeline import STRUCTURED_FIELD_NAMES, _tag_source_image
        classify_fields(response, response.rawOCR)
        _tag_source_image(response, source_name)

        # Visual analysis
        visual = run_visual_analysis(bgr_image, response)
        response.visual = visual

        # Collect results
        result["image_size"] = f"{width}x{height}"
        result["ocr_lines"] = len(response.rawOCR)
        result["uncertain_fields"] = response.uncertainFields

        # Classified fields
        result["classified"] = {
            "mrp": f"Rs. {response.mrp.value}" if response.mrp.found else "NOT FOUND",
            "netQuantity": response.netQuantity.rawValue if response.netQuantity.found else "NOT FOUND",
            "commodity": response.commodity.category if response.commodity.found else "NOT FOUND",
            "manufacturer": response.manufacturer.name if response.manufacturer.found else "NOT FOUND",
            "batchNumber": response.batchNumber.value if response.batchNumber.found else "NOT FOUND",
            "expiryDate": f"{response.expiryDate.day}/{response.expiryDate.month}/{response.expiryDate.year}" if response.expiryDate.found else "NOT FOUND",
        }

        # Visual evidence
        result["visual"] = {
            "font_size_entries": len(visual.relativeFontSizes),
            "netQuantityMedianRatio": visual.netQuantityMedianRatio,
            "contrast_entries": len(visual.contrast),
            "readability_entries": len(visual.readability),
            "has_quantity_clearance": visual.quantityClearance is not None,
            "pdp": visual.principalDisplayPanel.likelySourceImage if visual.principalDisplayPanel else None,
        }

        # Font sizes
        result["font_sizes"] = [
            {"field": e.field, "heightPx": e.heightPx, "ratioToNQ": e.ratioToNetQuantity}
            for e in visual.relativeFontSizes
        ]

        # Contrast
        result["contrast"] = [
            {"field": e.field, "stdDev": e.stdDev, "bucket": e.bucket}
            for e in visual.contrast
        ]

        # Readability
        result["readability"] = [
            {"field": e.field, "readability": e.readability, "reason": e.reason}
            for e in visual.readability
        ]

        # Clearance
        if visual.quantityClearance:
            c = visual.quantityClearance
            result["clearance"] = {
                "above": c.aboveRatio, "below": c.belowRatio,
                "left": c.leftRatio, "right": c.rightRatio,
            }
        else:
            result["clearance"] = None

        result["success"] = True

    except Exception as e:
        result["success"] = False
        result["errors"].append(traceback.format_exc())

    return result


def print_report(results: list):
    sep = "=" * 80
    for r in results:
        print(f"\n{sep}")
        print(f"IMAGE: {r['label']}")
        print(f"  Path: {r['path']}")
        if not r["success"]:
            print("  *** FAILED ***")
            for err in r["errors"]:
                print(err)
            continue

        print(f"  Size: {r['image_size']}, OCR lines: {r['ocr_lines']}")

        print("\n  CLASSIFIED FIELDS:")
        for k, v in r["classified"].items():
            print(f"    {k:20s}: {v}")

        if r["uncertain_fields"]:
            print("\n  UNCERTAIN/WARNINGS:")
            for u in r["uncertain_fields"]:
                print(f"    ⚠ {u}")

        print("\n  VISUAL — Font Sizes:")
        if r["font_sizes"]:
            for e in r["font_sizes"]:
                ratio = f"{e['ratioToNQ']:.3f}" if e["ratioToNQ"] is not None else "N/A"
                print(f"    {e['field']:20s}: {e['heightPx']:3d}px  ratio={ratio}")
            if r["visual"]["netQuantityMedianRatio"] is not None:
                print(f"    {'[nq/median ratio]':20s}: {r['visual']['netQuantityMedianRatio']:.3f}")
        else:
            print("    (none — no classified fields with bboxes)")

        print("\n  VISUAL — Contrast:")
        if r["contrast"]:
            for e in r["contrast"]:
                print(f"    {e['field']:20s}: std={e['stdDev']:6.2f}  [{e['bucket']:6s}]")
        else:
            print("    (none)")

        print("\n  VISUAL — Readability:")
        if r["readability"]:
            for e in r["readability"]:
                flag = "✓" if e["readability"] == "readable" else "✗"
                print(f"    {flag} {e['field']:20s}: {e['readability']}  ({e['reason']})")
        else:
            print("    (none)")

        print("\n  VISUAL — Quantity Clearance:")
        if r["clearance"]:
            c = r["clearance"]
            print(f"    above={c['above']:.3f}x  below={c['below']:.3f}x  left={c['left']:.3f}x  right={c['right']:.3f}x")
        else:
            print("    (not computed — netQuantity has no bbox)")

        pdp = r["visual"]["pdp"]
        print(f"\n  VISUAL — PDP heuristic: {pdp}")

    print(f"\n{sep}")
    passed = sum(1 for r in results if r["success"])
    print(f"\nSUMMARY: {passed}/{len(results)} images processed successfully")
    print(sep)


if __name__ == "__main__":
    results = []
    for label, path in IMAGE_PATHS.items():
        print(f"Processing: {label}...", flush=True)
        results.append(process_image(label, path))

    print_report(results)
