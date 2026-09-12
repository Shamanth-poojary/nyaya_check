"""
Thin wrapper around PaddleOCR's general OCR pipeline.

Phase 2 responsibility ONLY: given an image, return raw
(text, bbox, confidence) tuples. No classification, no field extraction,
no normalization -- that's Phase 4/5/6/7. Keep this file boring on purpose.
"""

import threading
from typing import List, NamedTuple, Union

_engine = None
_engine_lock = threading.Lock()


class OCRLine(NamedTuple):
    text: str
    bbox: tuple  # (xmin, ymin, xmax, ymax)
    confidence: float


def _get_engine():
    """
    Lazily initialize PaddleOCR once per process. Loading the engine is
    expensive (downloads/loads model weights), so we do it once and reuse
    it across requests rather than per-call.
    """
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                from paddleocr import PaddleOCR

                _engine = PaddleOCR(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=True,  # packaging photos are often held at an angle
                    # Mobile-tier models: much faster on CPU, slightly less accurate than
                    # the PP-OCRv6 medium default. Good for dev iteration; revisit once
                    # you're benchmarking real accuracy against your test image set.
                    # (English is already baked into the recognition model name below,
                    # so `lang=` is omitted -- passing both triggers a PaddleOCR warning.)
                    text_detection_model_name="PP-OCRv5_mobile_det",
                    text_recognition_model_name="en_PP-OCRv5_mobile_rec",
                    # Diagnostic: lower the internal confidence cutoffs so weak
                    # detections/recognitions surface in our output (as low-confidence
                    # lines) instead of being silently dropped before we ever see them.
                    # Defaults are roughly text_det_thresh=0.3, text_rec_score_thresh=0.5.
                    text_det_thresh=0.2,
                    text_det_box_thresh=0.4,
                    text_rec_score_thresh=0.1,
                )
    return _engine


def run_ocr(image_path: str) -> List[OCRLine]:
    """
    Run PaddleOCR on an image file.

    image_path: local path to the image on disk.
    Returns a flat list of OCRLine(text, bbox, confidence), skipping blanks.
    """
    engine = _get_engine()
    results = engine.predict(image_path)

    lines: List[OCRLine] = []
    for res in results:
        data = res.json.get("res", res.json)
        texts = data.get("rec_texts", [])
        scores = data.get("rec_scores", [])
        boxes = data.get("rec_boxes", [])

        for text, score, box in zip(texts, scores, boxes):
            if not text or not text.strip():
                continue
            xmin, ymin, xmax, ymax = (int(v) for v in box)
            lines.append(
                OCRLine(
                    text=text,
                    bbox=(xmin, ymin, xmax, ymax),
                    confidence=float(score),
                )
            )

    return lines
