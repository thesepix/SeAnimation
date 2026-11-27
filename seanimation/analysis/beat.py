"""Beat-/Tempo-Tracker (A4).

MVP: eigene Erkennung in numpy — Onset-Detektion via spektralem Fluss
(adaptiver Schwellwert), Tempo aus den Inter-Onset-Intervallen (Median,
geglättet), Beat-Phase per Snap auf erkannte Onsets (PLL-artig) plus
Free-Running zwischen den Beats. aubio/librosa bleiben optional für Step 2.

Step 2: externe Clock (Traktor MIDI/OSC) kann als alternative Clock-Quelle
angedockt werden, ohne diesen Tracker zu ändern.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np


class BeatState:
    """Zustand zu einem Zeitpunkt: beat_number, bpm, phase_in_beat (0..1),
    time_of_last_beat (Sekunden, Signal-Zeit), is_bar (jeder 4. Beat)."""

    def __init__(
        self,
        beat_number: int = 0,
        bpm: float = 120.0,
        phase: float = 0.0,
        time_of_last_beat: float = 0.0,
        is_bar: bool = False,
    ):
        self.beat_number = beat_number
        self.bpm = bpm
        self.phase = phase
        self.time_of_last_beat = time_of_last_beat
        self.is_bar = is_bar

    def envelope(self, now: float, tau: float = 0.25) -> float:
        """Beat-Envelope (Abschnitt 3.3.1): Impuls auf dem Beat, exponentielles
        Abklingen: env = exp(-dt / tau), dt = Zeit seit letztem Beat."""
        dt = max(0.0, now - self.time_of_last_beat)
        return math.exp(-dt / tau)

    def __repr__(self) -> str:
        return (
            f"BeatState(beat={self.beat_number}, bpm={self.bpm:.1f}, "
            f"phase={self.phase:.2f}, bar={self.is_bar})"
        )


class BeatTracker:
    """Hält BPM + Phase aktuell; liefert pro Analyse-Frame einen BeatState.

    update(features, now) erwartet das Feature-Dict des Analyzers
    (Key "onset" = spektraler Fluss) und die Signal-Zeit in Sekunden.
    """

    def __init__(
        self,
        samplerate: int = 48000,
        initial_bpm: float = 120.0,
        min_bpm: float = 60.0,
        max_bpm: float = 200.0,
    ):
        self.samplerate = samplerate
        self.min_period = 60.0 / max_bpm
        self.max_period = 60.0 / min_bpm
        self.period = 60.0 / initial_bpm
        self._beat_number = 0
        self._last_beat_time = 0.0
        self._next_beat_time: float | None = None
        self._last_onset_time: float | None = None
        self._intervals: deque[float] = deque(maxlen=12)
        self._flux_window: deque[float] = deque(maxlen=48)  # ~0,5 s bei hop=512/48 kHz
        self._refractory = 0.2  # s zwischen zwei Onsets (Periode bei 200 BPM = 0,3 s)
        self._last_event_time = -1.0

    @property
    def bpm(self) -> float:
        return 60.0 / self.period

    def update(self, features: dict, now: float) -> BeatState:
        flux = float(features.get("onset", 0.0))
        self._flux_window.append(flux)
        if self._detect_onset(flux, now):
            self._register_onset(now)
        if self._next_beat_time is None:
            self._last_beat_time = now
            self._next_beat_time = now + self.period
        while self._next_beat_time <= now:
            self._beat_number += 1
            self._last_beat_time = self._next_beat_time
            self._next_beat_time += self.period
        phase = (now - self._last_beat_time) / self.period
        phase = min(max(phase, 0.0), 1.0)
        return BeatState(
            beat_number=self._beat_number,
            bpm=self.bpm,
            phase=phase,
            time_of_last_beat=self._last_beat_time,
            is_bar=(self._beat_number % 4) == 0,
        )

    def _detect_onset(self, flux: float, now: float) -> bool:
        """Adaptiver Schwellwert über das jüngste Flux-Fenster + Refraktärzeit."""
        if len(self._flux_window) < 8:
            return False
        if now - self._last_event_time < self._refractory:
            return False
        arr = np.asarray(self._flux_window, dtype=np.float64)
        rest = arr[:-1]
        threshold = max(0.05, float(rest.mean() + 1.0 * rest.std()))
        if flux > threshold and flux > 1.5 * float(rest.mean()):
            self._last_event_time = now
            return True
        return False

    def _register_onset(self, t: float) -> None:
        # Tempo aus Inter-Onset-Intervallen (auf plausiblen Periodenbereich falten)
        if self._last_onset_time is not None:
            interval = t - self._last_onset_time
            cand = interval
            while cand > self.max_period:
                cand /= 2.0
            while cand < self.min_period:
                cand *= 2.0
            self._intervals.append(cand)
            if len(self._intervals) >= 3:
                target = float(np.median(self._intervals))
                self.period = 0.7 * self.period + 0.3 * target
            else:
                self.period = cand
        self._last_onset_time = t
        # Phasen-Snap (PLL-artig): Fehler zyklisch auf [-period/2, period/2]
        # falten und Grid auf den Onset ausrichten, solange |err| < 0.45*period.
        # Beat zählen (sonst würde die while-Schleife in update() nie feuern,
        # weil _next_beat_time immer knapp in der Zukunft liegt).
        if self._next_beat_time is not None:
            err = (t - self._next_beat_time + self.period / 2.0) % self.period - self.period / 2.0
            if abs(err) <= 0.45 * self.period:
                self._beat_number += 1
                self._last_beat_time = t
                self._next_beat_time = t + self.period
