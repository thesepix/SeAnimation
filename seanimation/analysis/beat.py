"""Beat-/Tempo-Tracker (A4).

MVP: eigene Erkennung aus dem Audiosignal — BPM + Beat-Phase pro Frame
(z. B. aubio.tempo über Onset-Zeiten, Phase per Interpolation zwischen
letztem und erwartetem Beat; Fallback: librosa.beat_track).

Step 2: externe Clock (Traktor MIDI/OSC) kann als alternative Clock-Quelle
angedockt werden, ohne diesen Tracker zu ändern.
"""

from __future__ import annotations


class BeatState:
    """Zustand zu einem Zeitpunkt: beat_number, bpm, phase_in_beat (0..1),
    time_of_last_beat (Sekunden), is_bar (jeder 4. Beat)."""

    def __init__(self, beat_number: int = 0, bpm: float = 120.0,
                 phase: float = 0.0, time_of_last_beat: float = 0.0, is_bar: bool = False):
        self.beat_number = beat_number
        self.bpm = bpm
        self.phase = phase
        self.time_of_last_beat = time_of_last_beat
        self.is_bar = is_bar

    def envelope(self, now: float, tau: float = 0.25) -> float:
        """Beat-Envelope (Abschnitt 3.3.1): Impuls auf dem Beat, exponentielles
        Abklingen: env = exp(-dt / tau), dt = Zeit seit letztem Beat."""
        dt = max(0.0, now - self.time_of_last_beat)
        import math
        return math.exp(-dt / tau)


class BeatTracker:
    """Hält BPM + Phase aktuell; liefert BeatState pro Frame."""

    def __init__(self, initial_bpm: float = 120.0):
        self.bpm = initial_bpm
        self._last_beat_time = 0.0
        self._beat_number = 0

    def update(self, features: dict, now: float) -> BeatState:
        # TODO(MVP): aubio/librosa-Tempo + Onset-Phase; BeatState ableiten.
        raise NotImplementedError
