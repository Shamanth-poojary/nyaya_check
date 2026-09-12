"""
Phase 3: OpenCV preprocessing pipeline.

Order: resize -> CLAHE contrast -> denoise -> (deskew: deferred, see deskew.py)

Design principle, straight from the project plan: preprocessing must be
MEASURED, not assumed. "Compare original versus preprocessed OCR accuracy.
Add preprocessing techniques incrementally." This pipeline is built to be
toggled on/off per-request (see routes/ocr.py's `preprocess` query param)
so you can A/B test against raw OCR on your own image set before deciding
which steps actually earn their place by default.
"""

from dataclasses import dataclass

import numpy as np

from app.preprocessing.contrast import apply_clahe
from app.preprocessing.denoise import denoise_image
from app.preprocessing.resize import resize_image


@dataclass
class PreprocessConfig:
    max_dimension: int = 1600
    apply_contrast: bool = True
    apply_denoise: bool = True
    # apply_deskew intentionally omitted -- see deskew.py


@dataclass
class PreprocessResult:
    image: np.ndarray
    scale: float  # multiply OCR bbox coords by (1/scale) to map back to the original photo


def preprocess(image: np.ndarray, config: PreprocessConfig = PreprocessConfig()) -> PreprocessResult:
    """Run the enabled preprocessing steps on a BGR image (as read by cv2)."""
    resized, scale = resize_image(image, config.max_dimension)

    processed = resized
    if config.apply_contrast:
        processed = apply_clahe(processed)
    if config.apply_denoise:
        processed = denoise_image(processed)

    return PreprocessResult(image=processed, scale=scale)
