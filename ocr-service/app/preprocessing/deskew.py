"""Deskew: NOT YET IMPLEMENTED. Read this before wiring it in.

Rotating a tilted photo upright requires re-projecting every OCR bounding
box through the INVERSE rotation matrix afterward, to keep boxes meaningful
in the original photo's coordinate space -- which Rules 7-10 (relative text
size, quantity-area spacing) depend on downstream. That's real, non-trivial
geometry, not a one-line addition like the other steps in this pipeline.

Deferred until you've confirmed -- from your own test image set -- that
skewed/rotated photos are actually causing misreads. The issues found so
far (missed manufacturer address, missed phone numbers) look like
low-contrast/small-text problems, which CLAHE + denoise already target,
not rotation problems. Revisit this if/when rotated photos in
`test_images/rotated/` show a measurable accuracy drop.

If/when you do implement this: estimate skew angle (e.g. via
cv2.minAreaRect on a thresholded mask, or via Hough line detection on
edges), rotate with cv2.warpAffine, and return BOTH the rotated image and
the rotation matrix (or its inverse) so the caller can map bboxes back.
"""

import numpy as np


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Currently a no-op passthrough. See module docstring."""
    return image
