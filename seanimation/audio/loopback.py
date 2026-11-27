"""WASAPI-Loopback-Quelle via sounddevice (PortAudio) (A1).

Nimmt auf, was der PC abspielt (System-Mix / "Was du hörst"). Unter Windows
erscheinen Loopback-Geräte ("... (loopback)") im WASAPI-Host-API und werden von
sounddevice automatisch gelistet — siehe `source.list_input_devices()`.
`device=None` wählt das System-Default-Gerät (Abschnitt 2).

sounddevice wird lazy in `start()` importiert, damit das Modul auch ohne
installierte Audio-Bibliothek importierbar bleibt (z. B. für Headless-Tests).
"""

from __future__ import annotations

import queue
from typing import Optional

import numpy as np

from .source import AudioSource


class LoopbackSource(AudioSource):
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
        import sounddevice as sd

        def callback(indata, frames, time_info, status):
            # indata: (frames, channels) float32 — Block in die Queue legen
            out_queue.put(indata.copy())

        self._stream = sd.InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            dtype="float32",
            latency="low",  # niedrige Latenz (N1: Audio->Bild < ~100 ms)
            callback=callback,
        )
        self._stream.start()
        # tatsächliche Samplerate des Geräts übernehmen (Analyzer/Tracker brauchen sie)
        self.samplerate = int(self._stream.samplerate) or self.samplerate

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
