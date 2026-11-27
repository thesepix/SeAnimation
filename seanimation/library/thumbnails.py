"""Thumbnail-Erzeugung für das UI-Raster (A5).

Video: mittlerer Frame via OpenCV; Bild: skaliert via PIL/OpenCV.
Ausgabe: numpy-RGBA-Array, das der Renderer als GL-Textur verwendet.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def make_thumbnail(path: Path, size: tuple[int, int] = (160, 90)) -> np.ndarray:
    """Thumbnail als RGBA-Array (H, W, 4) in Zielgröße."""
    # TODO(MVP): cv2.VideoCapture (Video) bzw. cv2.imread (Bild), Resize,
    # BGR->RGBA, np.ascontiguousarray.
    raise NotImplementedError
