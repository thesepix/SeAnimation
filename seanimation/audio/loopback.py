"""WASAPI-Loopback-Quelle via sounddevice (PortAudio).

Unter Windows erscheinen Loopback-Geräte ("... (loopback)") im WASAPI-Host-API
und werden von sounddevice automatisch gelistet. `device=None` wählt das
System-Default-Gerät (A1, Abschnitt 2).
"""

from __future__ import annotations

import queue
from typing import Optional

import numpy as np

from .source import AudioSource


class LoopbackSource(AudioSource):
    """Nimmt auf, was der PC abspielt (System-Mix / "Was du hörst")."""

    def __init__(
        self,
        device: Optional[int] = None,
        samplerate: int = 48000,
        blocksize: int = 512,
        channels: int = 2,
    ):
        self.device = device
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.channels = channels
        self._stream = None

    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        # TODO(MVP): sd.InputStream(device=self.device, ...) mit Callback,
        # der indata.copy() in out_queue legt; Latenz klein wählen (~20 ms).
        raise NotImplementedError

    def stop(self) -> None:
        # TODO(MVP): Stream stoppen/schließen.
        raise NotImplementedError
