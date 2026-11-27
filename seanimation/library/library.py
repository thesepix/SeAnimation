"""Animations-Bibliothek (A5–A6).

Scannt den Medien-Ordner (Bilder + Videos), erzeugt Metadaten (Dauer,
Größe, Thumbnail) und wählt Clips aus — ohne direkten Repeat (A6).

Zielausbau: ~100 Einträge im Ordner. MVP: 5 fest eingebaute Test-Animationen
(siehe render/effects.py); der Ordner-Scan der Bibliothek folgt im Zuge des MVP.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


@dataclass
class Clip:
    path: Path
    kind: str            # "video" | "image"
    duration: float      # Sekunden (0.0 bei Bildern)
    thumbnail: object = None  # PIL.Image oder numpy-Array, siehe thumbnails.py


class Library:
    def __init__(self, media_dir: Path, max_recent: int = 20):
        self.media_dir = Path(media_dir)
        self.clips: list[Clip] = []
        self._recent: list[Path] = []
        self.max_recent = max_recent

    def scan(self) -> None:
        """Ordner rekursiv nach Bildern/Videos durchsuchen, Metadaten + Thumbnails."""
        # TODO(MVP): os.walk / Path.rglob, cv2.VideoCapture für Dauer,
        # thumbnails.make_thumbnail; live File-Watcher für neue Dateien (Step 2).
        raise NotImplementedError

    def next_clip(self) -> Clip:
        """Zufälliger Clip; kürzlich gespielte (self._recent) ausgeschlossen (A6)."""
        # TODO(MVP): random.choice über Pool ohne _recent, dann zu _recent
        # hinzufügen (max_recent begrenzen).
        raise NotImplementedError

    def get(self, index: int) -> Clip:
        """Gezielter Zugriff per Thumbnail-Index (Klick in der UI)."""
        # TODO(MVP): Index-Wrapper mit Prüfung.
        raise NotImplementedError
