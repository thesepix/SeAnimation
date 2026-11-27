"""WavFileSource: WAV-Datei als Audioquelle (z. B. zum Testen ohne Loopback).

Später z. B.: python -m seanimation --wav mein-track.wav
Unterstützt PCM 8/16/24/32 bit. Float-WAVs u. a. Nicht-PCM-Formate liest das
stdlib-wave nicht — vorher konvertieren, z. B.:
    ffmpeg -i eingabe.wav -c:a pcm_s24le eingabe-24bit.wav
"""

from __future__ import annotations

import queue
import threading
import time
import wave
from pathlib import Path

import numpy as np

from .source import AudioSource


class WavFileSource(AudioSource):
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
        """WAV laden -> float32-Array (n, channels); setzt self.samplerate."""
        try:
            w = wave.open(str(self.path), "rb")
        except wave.Error as e:
            raise ValueError(
                f"{self.path}: kein lesbares PCM-WAV ({e}). Bitte konvertieren, z. B.: "
                "ffmpeg -i eingabe.wav -c:a pcm_s24le eingabe-24bit.wav"
            ) from e
        with w:
            channels = w.getnchannels()
            sampwidth = w.getsampwidth()
            self.samplerate = w.getframerate()
            raw = w.readframes(w.getnframes())
        if sampwidth == 1:
            data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        elif sampwidth == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 3:
            # 24-bit little-endian -> int32 mit Vorzeichenerweiterung
            b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
            v = (
                b[:, 0].astype(np.int32)
                | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16)
            )
            v = np.where(v & 0x800000, v - 0x1000000, v)
            data = v.astype(np.float32) / 8388608.0
        elif sampwidth == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(
                f"Nicht unterstützte Sample-Breite: {sampwidth} Bytes (nur PCM 8/16/24/32 bit)"
            )
        arr = data.reshape(-1, channels)
        self._data = arr
        return arr

    def ensure_loaded(self) -> np.ndarray:
        """Daten laden (einmalig gecacht) und samplerate setzen — vor start() aufrufen,
        damit die Samplerate für den Analyzer bekannt ist."""
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
