"""Contrast enhancement: CLAHE on the luminance channel only.

Targets glare and low-contrast text on glossy/busy packaging (per the
project plan: "CLAHE for glare reduction"). Working in LAB color space and
only touching the L channel preserves the image's color information, which
the detection network may also rely on -- unlike converting to flat
grayscale, which throws color away entirely.
"""

import cv2
import numpy as np


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple = (8, 8),
) -> np.ndarray:
    """Apply CLAHE to a BGR image's luminance channel, return BGR."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_eq = clahe.apply(l)

    merged = cv2.merge((l_eq, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
