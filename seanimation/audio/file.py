"""AudioFileSource: Audio-Datei als Quelle via soundfile (libsndfile).

Formate: WAV, FLAC, OGG/Vorbis, MP3 (libsndfile >= 1.1), AIFF, ...
Aufruf: python -m seanimation --file mein-track.flac   (Alias: --wav)

soundfile wird lazy in load() importiert; ohne soundfile greift der
stdlib-Fallback WavFileSource (nur PCM-WAV).
"""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path

import numpy as np

from .source import AudioSource


class AudioFileSource(AudioSource):
    def __init__(
        self,
        path,
        blocksize: int = 512,
        realtime: bool = True,
        loop: bool = False,
    ):
        self.path = Path(path)
        self.blocksize = blocksize
        self.realtime = realtime
        self.loop = loop
        self.samplerate: int = 0
        self._data: np.ndarray | None = None
        self._stop = False
        self._thread: threading.Thread | None = None

    def load(self) -> np.ndarray:
        """Datei dekodieren -> float32-Array (n, channels); setzt self.samplerate."""
        import soundfile as sf

        data, sr = sf.read(str(self.path), dtype="float32", always_2d=True)
        self.samplerate = int(sr)
        self._data = np.ascontiguousarray(data, dtype=np.float32)
        return self._data

    def ensure_loaded(self) -> np.ndarray:
        """Daten laden (einmalig gecacht) — vor start() aufrufen, damit die
        Samplerate für den Analyzer bekannt ist."""
        if self._data is None:
            self.load()
        return self._data

    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        data = self.ensure_loaded()
        self._stop = False

        def run() -> None:
            i = 0
            while not self._stop:
                if i >= data.shape[0]:
                    if not self.loop:
                        break
                    i = 0
                out_queue.put(data[i : i + self.blocksize].copy())
                i += self.blocksize
                if self.realtime:
                    time.sleep(self.blocksize / self.samplerate)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop = True
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
