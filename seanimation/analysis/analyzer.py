"""Audio-Analyse (A3): FFT, Frequenzbänder, Onset-/Kick-Detektion.

Eingang: PCM-Blöcke (float32, (n, channels)) aus der AudioSource-Queue.
Ausgang pro Analyse-Frame: Feature-Dict mit Band-Energien (bass/mid/high),
spektralem Fluss (Onset), Kick-Anteil und Signal-Zeit — für Renderer und
BeatTracker.
"""

from __future__ import annotations

import numpy as np

# Frequenzgrenzen der Bänder in Hz
BAND_BASS = (20.0, 150.0)
BAND_MID = (150.0, 2000.0)
BAND_HIGH = (2000.0, 16000.0)


class Analyzer:
    """Gleitendes Fenster (Hann) + numpy-FFT; Band-Energien normiert auf
    Gesamtenergie; Onset = positiver spektraler Fluss; Kick = Anstieg im
    Bassband (A3)."""

    def __init__(self, samplerate: int = 48000, fft_size: int = 2048, hop: int = 512):
        self.samplerate = samplerate
        self.fft_size = fft_size
        self.hop = hop
        self._window = np.hanning(fft_size).astype(np.float32)
        self._buffer = np.zeros(0, dtype=np.float32)
        self._prev_mag: np.ndarray | None = None
        self._prev_bass = 0.0
        self.frame_index = 0
        freqs = np.fft.rfftfreq(fft_size, d=1.0 / samplerate)
        self._band_masks = {
            "bass": (freqs >= BAND_BASS[0]) & (freqs < BAND_BASS[1]),
            "mid": (freqs >= BAND_MID[0]) & (freqs < BAND_MID[1]),
            "high": (freqs >= BAND_HIGH[0]) & (freqs < BAND_HIGH[1]),
        }

    def process(self, block: np.ndarray) -> list[dict]:
        """Ein PCM-Block -> Liste von Feature-Dicts (0..n Frames, je nach Hop)."""
        block = np.asarray(block, dtype=np.float32)
        mono = block.mean(axis=1) if block.ndim == 2 else block
        self._buffer = np.concatenate([self._buffer, mono])
        frames: list[dict] = []
        while self._buffer.size >= self.fft_size:
            frame = self._buffer[: self.fft_size] * self._window
            self._buffer = self._buffer[self.hop :]
            mag = np.abs(np.fft.rfft(frame)).astype(np.float64)
            norm = float(np.sqrt((mag**2).sum())) + 1e-9
            bands = {
                name: float((mag[mask] ** 2).sum() / norm**2)
                for name, mask in self._band_masks.items()
            }
            if self._prev_mag is not None:
                flux = float(np.maximum(mag - self._prev_mag, 0.0).sum() / norm)
            else:
                flux = 0.0
            kick = max(0.0, bands["bass"] - self._prev_bass)
            self._prev_mag = mag
            self._prev_bass = bands["bass"]
            t = self.frame_index * self.hop / self.samplerate
            self.frame_index += 1
            frames.append(
                {
                    "time": t,
                    "bass": bands["bass"],
                    "mid": bands["mid"],
                    "high": bands["high"],
                    "onset": flux,
                    "kick": kick,
                }
            )
        return frames
