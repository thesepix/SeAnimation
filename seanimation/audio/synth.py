"""SynthSource: synthetische Audioquelle für Tests ohne Audiohardware.

Erzeugt Kick (pitch-fallender Sinus, 120->40 Hz) + Click (1,5 kHz) auf jedem
Beat bei gegebener BPM. `realtime=False` pusht die Blöcke so schnell wie
möglich — ideal für den Selftest (`python -m seanimation --selftest`).
"""

from __future__ import annotations

import queue
import threading
import time

import numpy as np

from .source import AudioSource


class SynthSource(AudioSource):
    def __init__(
        self,
        bpm: float = 124.0,
        samplerate: int = 48000,
        blocksize: int = 512,
        duration: float = 10.0,
        realtime: bool = True,
    ):
        self.bpm = bpm
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.duration = duration
        self.realtime = realtime
        self._stop = False
        self._thread: threading.Thread | None = None

    def generate(self) -> np.ndarray:
        """Mono-Signal (float32) der Länge duration * samplerate."""
        n = int(self.duration * self.samplerate)
        sig = np.zeros(n, dtype=np.float32)
        period = 60.0 / self.bpm
        for bt in np.arange(0.0, self.duration, period):
            i0 = int(bt * self.samplerate)
            m = min(int(0.18 * self.samplerate), n - i0)
            if m <= 0:
                continue
            tt = np.arange(m) / self.samplerate
            freq = 40.0 + 80.0 * np.exp(-tt / 0.03)
            phase = 2.0 * np.pi * np.cumsum(freq) / self.samplerate
            sig[i0 : i0 + m] += (0.9 * np.sin(phase) * np.exp(-tt / 0.06)).astype(np.float32)
            mc = min(int(0.02 * self.samplerate), n - i0)
            if mc > 0:
                tc = np.arange(mc) / self.samplerate
                sig[i0 : i0 + mc] += (
                    0.5 * np.sin(2.0 * np.pi * 1500.0 * tc) * np.exp(-tc / 0.002)
                ).astype(np.float32)
        return np.clip(sig, -1.0, 1.0)

    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        sig = self.generate()
        self._stop = False

        def run() -> None:
            i = 0
            while not self._stop and i < sig.size:
                blk = sig[i : i + self.blocksize]
                out_queue.put(np.stack([blk, blk], axis=1))  # Stereo-Block
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
