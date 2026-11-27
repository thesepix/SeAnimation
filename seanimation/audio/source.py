"""AudioSource-Abstraktion (A2).

Alle Audioeingänge liefern PCM-Frames (interleaved float32) in eine
gemeinsame Queue / einen Ringpuffer.

- MVP: `LoopbackSource` — WASAPI-Loopback ("Was du hörst") über sounddevice.
- Step 2: `NetworkSource` — Audio-Stream vom Traktor-Laptop (z. B. VBAN/RTP).
"""

from __future__ import annotations

import abc
import queue
from typing import Optional

import numpy as np


class AudioSource(abc.ABC):
    """Abstrakte Audioquelle: liefert PCM-Blöcke in eine Queue."""

    @abc.abstractmethod
    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        """Quelle starten; PCM-Blöcke (float32) in out_queue legen."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Quelle stoppen und Ressourcen freigeben."""


def get_default_source(device: Optional[int] = None) -> AudioSource:
    """MVP: Standard-/erstes verfügbares Windows-Audiogerät als Loopback-Quelle."""
    from .loopback import LoopbackSource

    return LoopbackSource(device=device)
