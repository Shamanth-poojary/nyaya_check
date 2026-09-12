"""Resize: downscale large photos before the rest of the pipeline runs.

Inference/processing time scales with pixel count, and phone photos are
often much bigger than needed for text detection. This step never upscales.
"""

from typing import Tuple

import cv2
import numpy as np


def resize_image(image: np.ndarray, max_dimension: int = 1600) -> Tuple[np.ndarray, float]:
    """
    Downscale `image` so its longest side is at most `max_dimension`.

    Returns (resized_image, scale) where scale = resized_size / original_size.
    scale is 1.0 (no-op) if the image is already small enough.
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_dimension:
        return image, 1.0

    scale = max_dimension / longest
    new_size = (round(w * scale), round(h * scale))
    resized = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return resized, scale
