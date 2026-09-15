"""Debug script to print raw OCR lines for Parle-G and Britannia images."""
import io
import sys
import os
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from PIL import Image
from app.ocr.normalize import merge_split_lines
from app.ocr.paddle import run_ocr
from app.preprocessing.resize import resize_image
from app.schemas.response import BoundingBox, ExtractionResponse, RawOCRLine, empty_response
from app.classification.fields import classify_fields
from app.pipeline import _tag_source_image

IMAGES = {
    "busy_background (Parle-G)": Path("test_images/busy_background/ChatGPT Image Sep 15, 2026, 09_17_00 AM.png"),
    "mixed (Britannia Marie Gold)": Path("test_images/mixed/ChatGPT Image Sep 15, 2026, 09_20_12 AM.png"),
    "rotated (Tata Tea)": Path("test_images/rotated/ChatGPT Image Sep 15, 2026, 09_23_01 AM.png"),
    "glossy (Lays)": Path("test_images/glossy/ChatGPT Image Sep 15, 2026, 09_18_39 AM.png"),
}

for label, img_path in IMAGES.items():
    print(f"\n{'='*70}")
    print(f"IMAGE: {label}")
    pil = Image.open(img_path).convert("RGB")
    w, h = pil.size
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    ocr_img, scale = resize_image(bgr, max_dimension=1600)
    inv = 1.0 / scale

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    cv2.imwrite(tmp_path, ocr_img)
    try:
        lines = run_ocr(tmp_path)
        lines = merge_split_lines(lines)
    finally:
        os.remove(tmp_path)

    response = empty_response(image_id=img_path.name, width=w, height=h)
    response.rawOCR = [
        RawOCRLine(
            text=l.text,
            bbox=BoundingBox(
                xmin=round(l.bbox[0]*inv), ymin=round(l.bbox[1]*inv),
                xmax=round(l.bbox[2]*inv), ymax=round(l.bbox[3]*inv),
            ),
            confidence=l.confidence, sourceImage=img_path.name,
        )
        for l in lines
    ]

    print("\nRAW OCR LINES (ymin sorted):")
    for i, l in enumerate(sorted(response.rawOCR, key=lambda x: x.bbox.ymin)):
        print(f"  [{i:02d}] conf={l.confidence:.3f} y={l.bbox.ymin:4d}-{l.bbox.ymax:4d}  {l.text!r}")

    classify_fields(response, response.rawOCR)
    print(f"\nCLASSIFIED: mrp={response.mrp.value} nq={response.netQuantity.rawValue} batch={response.batchNumber.value!r}")
    if response.uncertainFields:
        for u in response.uncertainFields:
            print(f"  WARN: {u}")
