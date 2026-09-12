"""Denoise: reduce sensor/compression noise without blurring text edges.

Uses a bilateral filter rather than aggressive non-local-means denoising --
bilateral filtering smooths flat regions (background, plastic sheen) while
preserving sharp edges, which matters because small printed text is exactly
the kind of detail heavier denoising tends to blur away.
"""

import cv2
import numpy as np


def denoise_image(image: np.ndarray, strength: int = 7) -> np.ndarray:
    """Apply a light bilateral filter to a BGR image."""
    sigma = strength * 10
    return cv2.bilateralFilter(image, d=5, sigmaColor=sigma, sigmaSpace=sigma)
