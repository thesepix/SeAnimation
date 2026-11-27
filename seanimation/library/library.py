"""Animations-Bibliothek (A5–A6).

Scannt den Medien-Ordner (Bilder + Videos), erzeugt Thumbnails und wählt
Clips ohne direkten Repeat aus. Zielausbau: ~100 Einträge; MVP: 5 eingebaute
Effekte (render/effects.py) + beliebige Clips aus MEDIA_DIR.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

THUMB_SIZE = (160, 90)


@dataclass
class Clip:
    path: Path
    kind: str            # "video" | "image"
    duration: float      # Sekunden (0.0 bei Bildern)
    n_frames: int
    thumbnail: np.ndarray | None = None  # RGBA uint8 (THUMB_SIZE)


def _make_thumbnail(rgba: np.ndarray, size=THUMB_SIZE) -> np.ndarray:
    img = Image.fromarray(rgba, mode="RGBA").resize(size, Image.BILINEAR)
    return np.ascontiguousarray(np.array(img), dtype=np.uint8)


class Library:
    def __init__(self, media_dir, max_recent: int = 20):
        self.media_dir = Path(media_dir)
        self.clips: list[Clip] = []
        self._recent: list[Path] = []
        self.max_recent = max_recent

    def scan(self) -> list[Clip]:
        """Ordner rekursiv nach Bildern/Videos durchsuchen, Metadaten + Thumbnails."""
        from .clip_player import ClipPlayer

        self.clips = []
        if not self.media_dir.is_dir():
            return self.clips
        paths = sorted(
            p for p in self.media_dir.rglob("*")
            if p.suffix.lower() in VIDEO_EXTS | IMAGE_EXTS and p.is_file()
        )
        for p in paths:
            try:
                player = ClipPlayer(p)
                kind = player.kind
                duration = player.n_frames / player.fps if kind == "video" else 0.0
                thumb = _make_thumbnail(player.first_frame())
                player.close()
                self.clips.append(Clip(p, kind, duration, player.n_frames, thumb))
            except Exception as e:
                print(f"  [library] überspringe {p.name}: {e}")
        return self.clips

    def clips_of_kind(self, kind: str) -> list[Clip]:
        return [c for c in self.clips if c.kind == kind]

    def next_clip(self, kind: str | None = None) -> Clip | None:
        """Zufälliger Clip (ggf. nur bestimmter kind); kürzlich gespielte ausgeschlossen (A6)."""
        pool = self.clips_of_kind(kind) if kind else self.clips
        pool = [c for c in pool if c.path not in self._recent] or pool
        if not pool:
            return None
        clip = random.choice(pool)
        self._recent.append(clip.path)
        self._recent = self._recent[-self.max_recent :]
        return clip

    def get(self, index: int) -> Clip:
        return self.clips[index]
