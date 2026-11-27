"""ClipPlayer: Video/Bild als Quelle — mit Prefetch-Decode-Thread (Performance).

Video: Decode läuft in einem Hintergrund-Thread (Prefetch-Queue, bounded,
neuestes Frame gewinnt), downscale auf max 720p, Y-Flip einmalig im Thread.
Der Renderer nimmt nur `latest_frame()` — der Haupt-Thread dekodiert nicht mehr.

- Smooth (Default, frames_per_beat=0): flüssige Wiedergabe (neuestes dekodiertes Frame)
- Frame-Step (frames_per_beat>0): get_frame(beat) — genau N Frames pro Beat
"""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .library import IMAGE_EXTS, VIDEO_EXTS

MAX_TEX_H = 720  # Videos höher als 720p werden vor dem Upload downscaled


class ClipPlayer:
    def __init__(self, path, frames_per_beat: int = 0, prefetch: bool = False):
        self.path = Path(path)
        self.frames_per_beat = max(0, frames_per_beat)  # 0 = smooth
        self.kind = "video" if self.path.suffix.lower() in VIDEO_EXTS else "image"
        self.cap: cv2.VideoCapture | None = None
        self.n_frames = 0
        self.fps = 0.0
        self.image: np.ndarray | None = None  # RGBA uint8
        self._cur_idx = -1
        self._last_frame: np.ndarray | None = None
        self._smooth_pos = 0.0
        self.frame_seq = 0          # erhöht sich pro neuem Frame (Renderer: Upload skip)
        self._flipped = False       # True wenn Frames bereits Y-geflipped sind
        self._frame_q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=8)
        self._stop = False
        self._thread: threading.Thread | None = None
        self._open()
        if prefetch and self.kind == "video":
            self.start_prefetch()

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

    # ---------- Prefetch (Smooth-Video) ----------
    def start_prefetch(self) -> None:
        """Decode-Thread starten: liest fortlaufend, legt Frames in eine bounded Queue."""
        if self.kind != "video" or self._thread is not None:
            return
        self._stop = False

        def run() -> None:
            cap = self.cap
            assert cap is not None
            while not self._stop:
                try:
                    ok, frame = cap.read()
                except Exception:
                    break  # cap wurde geschlossen
                if self._stop:
                    break
                if not ok:  # Loop
                    try:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        break
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                h, w = frame.shape[:2]
                if h > MAX_TEX_H:
                    scale = MAX_TEX_H / h
                    frame = cv2.resize(frame, (max(1, int(w * scale)), MAX_TEX_H),
                                       interpolation=cv2.INTER_AREA)
                frame = np.ascontiguousarray(frame[::-1])  # Y-Flip einmalig im Decode-Thread
                self._last_frame = frame
                self.frame_seq += 1
                try:
                    self._frame_q.put_nowait(frame)
                except queue.Full:
                    pass  # Queue voll -> neues Frame gewinnt
                time.sleep(1.0 / max(1.0, self.fps))  # im Video-Tempo dekodieren

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        self._flipped = True

    def latest_frame(self) -> np.ndarray | None:
        """Neuestes dekodiertes Frame (None wenn noch keins)."""
        while True:
            try:
                self._last_frame = self._frame_q.get_nowait()
            except queue.Empty:
                break
        return self._last_frame

    # ---------- Frame-Step (optional) ----------
    @staticmethod
    def frame_index_for_beat(beat_number: int, total_frames: int, frames_per_beat: int = 1) -> int:
        if total_frames <= 0:
            return 0
        return (int(beat_number) * max(1, frames_per_beat)) % total_frames

    def _read_upto(self, idx: int) -> np.ndarray:
        assert self.cap is not None
        if idx < self._cur_idx:
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
                self.frame_seq += 1
        if self._last_frame is not None:
            return np.ascontiguousarray(self._last_frame, dtype=np.uint8)
        return np.zeros((720, 1280, 4), dtype=np.uint8)

    def get_frame(self, beat_number: int) -> np.ndarray:
        """Frame-Step: Frame zur Beat-Nummer."""
        if self.image is not None:
            return self.image
        idx = self.frame_index_for_beat(beat_number, self.n_frames, max(1, self.frames_per_beat))
        return self._read_upto(idx)

    def read_smooth(self, dt: float) -> np.ndarray:
        """Synchroner Smooth-Pfad (ohne Prefetch, z. B. Tests): fps*dt weiter, Loop."""
        if self.image is not None:
            return self.image
        self._smooth_pos += max(0.0, self.fps) * max(0.0, dt)
        idx = int(self._smooth_pos) % max(1, self.n_frames)
        return self._read_upto(idx)

    def first_frame(self) -> np.ndarray:
        if self.image is not None:
            return self.image
        return self.get_frame(0)

    def close(self) -> None:
        self._stop = True
        if self._thread is not None:
            self._thread.join(timeout=3.0)  # Thread sauber beenden, BEVOR cap freigegeben wird
            self._thread = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
