"""Audio-Analyse (A3): FFT, Frequenzbänder, Onset-/Kick-Detektion.

Eingang: PCM-Blöcke aus dem Ringpuffer.
Ausgang pro Frame: Feature-Dict mit Band-Energien (bass/mid/high),
Onset-Stärke und Roh-Spektrum — für Renderer und BeatTracker.
"""

from __future__ import annotations

import numpy as np

# Frequenzgrenzen der Bänder in Hz
BAND_BASS = (20, 150)
BAND_MID = (150, 2000)
BAND_HIGH = (2000, 16000)


class Analyzer:
    """Gleitendes Fenster + numpy-FFT; spektraler Fluss für Onsets;
    Kick-Detektion im Bassband (A3)."""

    def __init__(self, samplerate: int = 48000, fft_size: int = 2048, hop: int = 512):
        self.samplerate = samplerate
        self.fft_size = fft_size
        self.hop = hop
        self._window = np.hanning(fft_size)
        self._prev_spectrum: np.ndarray | None = None

    def process(self, block: np.ndarray) -> dict:
        """Ein PCM-Block -> dict(bass, mid, high, onset, spectrum)."""
        # TODO(MVP): Fenster puffern, np.fft.rfft, Band-Energien summieren,
        # Onset = positiver spektraler Fluss vs. _prev_spectrum, Kick im Bassband.
        raise NotImplementedError
