"""ClipPlayer: Video/Bild als Quelle.

- Smooth (Default, frames_per_beat=0): Video läuft flüssig mit eigener fps
  (read_smooth(dt) schaltet pro Render-Frame weiter); Beat-Sync kommt über
  Shader-Effekte + Auto-Wechsel auf Bar-Grenzen.
- Frame-Step (frames_per_beat>0): genau N Frames pro Beat (Stop-Motion).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .library import IMAGE_EXTS, VIDEO_EXTS


class ClipPlayer:
    def __init__(self, path, frames_per_beat: int = 0):
        self.path = Path(path)
        self.frames_per_beat = max(0, frames_per_beat)  # 0 = smooth
        self.kind = "video" if self.path.suffix.lower() in VIDEO_EXTS else "image"
        self.cap: cv2.VideoCapture | None = None
        self.n_frames = 0
        self.fps = 0.0
        self.image: np.ndarray | None = None  # RGBA uint8
        self._cur_idx = -1
        self._last_frame: np.ndarray | None = None
        self._smooth_pos = 0.0  # float Frame-Cursor für Smooth-Modus
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

    def _read_upto(self, idx: int) -> np.ndarray:
        """Sequentiell bis Frame idx lesen (mit Loop am Ende)."""
        assert self.cap is not None
        if idx < self._cur_idx:  # Loop: zurück auf 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._cur_idx = -1
            self._last_frame = None
        while self._cur_idx < idx:
            ok, frame = self.cap.read()
            if not ok:
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
        return np.zeros((720, 1280, 4), dtype=np.uint8)

    def get_frame(self, beat_number: int) -> np.ndarray:
        """Frame-Step-Modus: Frame zur Beat-Nummer (RGBA)."""
        if self.image is not None:
            return self.image
        idx = self.frame_index_for_beat(beat_number, self.n_frames, max(1, self.frames_per_beat))
        return self._read_upto(idx)

    def read_smooth(self, dt: float) -> np.ndarray:
        """Smooth-Modus: um fps*dt Frames weiterschalten (mit Loop), RGBA zurück."""
        if self.image is not None:
            return self.image
        self._smooth_pos += max(0.0, self.fps) * max(0.0, dt)
        idx = int(self._smooth_pos) % max(1, self.n_frames)
        return self._read_upto(idx)

    def first_frame(self) -> np.ndarray:
        """Erstes Frame (für Thumbnails)."""
        if self.image is not None:
            return self.image
        return self.get_frame(0)

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
