"""ClipPlayer: Video/Bild als beat-synchronisierte Quelle (Frame-Step, Abschnitt 3.3.2).

Video: pro Beat wird genau `frames_per_beat` Frame weitergeschaltet
(Stop-Motion), Loop über die Gesamtlänge. Bild: statisches Frame, Effekte
laufen über Shader-Uniforms (Kick-Puls, Wobble).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .library import IMAGE_EXTS, VIDEO_EXTS


class ClipPlayer:
    def __init__(self, path, frames_per_beat: int = 1):
        self.path = Path(path)
        self.frames_per_beat = max(1, frames_per_beat)
        self.kind = "video" if self.path.suffix.lower() in VIDEO_EXTS else "image"
        self.cap: cv2.VideoCapture | None = None
        self.n_frames = 0
        self.fps = 0.0
        self.image: np.ndarray | None = None  # RGBA uint8
        self._cur_idx = -1
        self._last_frame: np.ndarray | None = None
        self._open()

    def _open(self) -> None:
        if self.kind == "video":
            self.cap = cv2.VideoCapture(str(self.path))
            if not self.cap.isOpened():
                raise ValueError(f"Video nicht dekodierbar: {self.path}")
            self.n_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 30.0
        else:
            img = Image.open(self.path).convert("RGBA")
            self.image = np.ascontiguousarray(np.array(img), dtype=np.uint8)
            self.n_frames = 1

    @staticmethod
    def frame_index_for_beat(beat_number: int, total_frames: int, frames_per_beat: int = 1) -> int:
        """Frame-Step: Frame-Index aus der Beat-Nummer (jede Änderung auf dem Beat)."""
        if total_frames <= 0:
            return 0
        return (int(beat_number) * max(1, frames_per_beat)) % total_frames

    def get_frame(self, beat_number: int) -> np.ndarray:
        """Aktuelles Frame (RGBA uint8) für die gegebene Beat-Nummer."""
        if self.image is not None:
            return self.image
        idx = self.frame_index_for_beat(beat_number, self.n_frames, self.frames_per_beat)
        assert self.cap is not None
        if idx < self._cur_idx:  # Loop: zurück auf 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._cur_idx = -1
            self._last_frame = None
        while self._cur_idx < idx:
            ok, frame = self.cap.read()
            if not ok:
                # Ende erreicht -> Loop
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self._cur_idx = -1
                ok, frame = self.cap.read()
                if not ok:
                    break
            self._cur_idx += 1
            if frame is not None:
                self._last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        if self._last_frame is not None:
            return np.ascontiguousarray(self._last_frame, dtype=np.uint8)
        # Fallback: schwarzes Frame in Konsolengröße
        return np.zeros((720, 1280, 4), dtype=np.uint8)

    def first_frame(self) -> np.ndarray:
        """Erstes Frame (für Thumbnails)."""
        if self.image is not None:
            return self.image
        return self.get_frame(0)

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
