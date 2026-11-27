"""Dev-Selftest der Beat-Pipeline — läuft ohne Audiohardware/GPU.

Aufruf: python -m seanimation --selftest [--bpm 124]

Erzeugt ein synthetisches Signal (Kick + Click auf jedem Beat bei bekannter
BPM), schickt es durch Analyzer -> BeatTracker und prüft erkannte BPM und
Phasenlage (letzter Beat nahe am echten Beat-Zeitpunkt).
"""

from __future__ import annotations

import queue

import numpy as np

from .analysis.analyzer import Analyzer
from .analysis.beat import BeatTracker
from .audio.synth import SynthSource


def run_selftest(
    bpm: float = 124.0,
    duration: float = 8.0,
    samplerate: int = 48000,
    tol: float = 3.0,
    verbose: bool = True,
) -> bool:
    synth = SynthSource(bpm=bpm, samplerate=samplerate, duration=duration, realtime=False)
    q: "queue.Queue" = queue.Queue()
    synth.start(q)
    analyzer = Analyzer(samplerate=samplerate)
    tracker = BeatTracker(samplerate=samplerate)
    last_state = None
    while True:
        try:
            block = q.get(timeout=0.5)
        except queue.Empty:
            break
        for features in analyzer.process(block):
            last_state = tracker.update(features, features["time"])
    synth.stop()

    period = 60.0 / bpm
    true_beats = np.arange(0.0, duration, period)
    bpm_ok = abs(tracker.bpm - bpm) <= tol
    if last_state is not None and true_beats.size:
        dist = float(np.min(np.abs(last_state.time_of_last_beat - true_beats)))
        align_ok = dist <= 0.3 * period
    else:
        dist = float("nan")
        align_ok = False
    ok = bpm_ok and align_ok
    if verbose:
        print(f"Selftest: Synth-Signal {bpm:.1f} BPM, {duration:.1f} s, {samplerate} Hz")
        print(f"  erkannt: {tracker.bpm:.2f} BPM (Toleranz ±{tol}) -> {'OK' if bpm_ok else 'FAIL'}")
        print(
            f"  letzter Beat bei t={last_state.time_of_last_beat:.3f}s, "
            f"Abweichung zum echten Beat {dist * 1000:.0f} ms -> {'OK' if align_ok else 'FAIL'}"
        )
        print(f"  {last_state}")
        print("  ERGEBNIS: " + ("PASS" if ok else "FAIL"))
    return ok
