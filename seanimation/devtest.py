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


def _make_file_source(path, realtime: bool):
    """AudioFileSource (soundfile: WAV/FLAC/MP3/OGG/...), Fallback: WavFileSource."""
    try:
        import soundfile  # noqa: F401

        from .audio.file import AudioFileSource

        return AudioFileSource(path, realtime=realtime, loop=False)
    except ImportError:
        from .audio.wavfile import WavFileSource

        return WavFileSource(path, realtime=realtime, loop=False)


def run_file_analysis(path, realtime: bool = False, verbose: bool = True, max_beats_print: int = 16) -> dict:
    """Audio-Datei (WAV/FLAC/MP3/...) durch die Pipeline: FileSource -> Analyzer -> BeatTracker.

    realtime=False (Default): schneller Durchlauf der ganzen Datei, danach
    erkannte BPM + Beats ausgeben. Aufruf: python -m seanimation --file <datei>
    """
    src = _make_file_source(path, realtime=realtime)
    src.ensure_loaded()  # setzt samplerate
    sr = src.samplerate
    q: "queue.Queue" = queue.Queue()
    src.start(q)
    analyzer = Analyzer(samplerate=sr)
    tracker = BeatTracker(samplerate=sr)
    beats: list[tuple[int, float, float, bool]] = []
    last_state = None
    while True:
        try:
            block = q.get(timeout=1.0 if realtime else 0.5)
        except queue.Empty:
            break
        for features in analyzer.process(block):
            st = tracker.update(features, features["time"])
            if st.beat_number > 0 and (not beats or beats[-1][0] != st.beat_number):
                beats.append((st.beat_number, st.time_of_last_beat, st.bpm, st.is_bar))
            last_state = st
    src.stop()
    if verbose:
        print(f"Datei-Analyse: {path} ({sr} Hz)")
        print(f"  erkannte BPM (Endstand): {tracker.bpm:.2f}")
        print(f"  erkannte Beats: {len(beats)}")
        for bn, t, bpm, bar in beats[-max_beats_print:]:
            print(f"    beat {bn:3d}  t={t:7.3f}s  bpm={bpm:6.1f}  {'BAR' if bar else ''}")
    return {"bpm": tracker.bpm, "beats": beats, "state": last_state, "samplerate": sr}


# Rückwärtskompatibler Alias (alt: --wav)
run_wav_analysis = run_file_analysis


def run_tap_mode(path=None, verbose: bool = True) -> dict:
    """Interaktiver Beat-Tap (A12): Enter = Tap im Takt, q = Ende.

    Mit --file wird die Datei in Echtzeit gestreamt (zum Mitverfolgen), ohne
    Datei wird nur getappt. Der Tap überschreibt die Auto-Erkennung für 8 s.
    Aufruf: python -m seanimation --tap [--file track.flac]
    """
    import sys
    import threading
    import time

    from .analysis.beat import BeatTracker

    tracker = BeatTracker(samplerate=48000)
    analyzer = Analyzer(samplerate=48000)
    stop = threading.Event()
    t0 = time.monotonic()

    def tap_reader() -> None:
        for line in sys.stdin:
            if line.strip().lower() in ("q", "quit", "exit"):
                stop.set()
                return
            now = time.monotonic() - t0
            tracker.tap(now)
            if verbose:
                print(f"  tap @ {now:7.3f}s -> bpm={tracker.bpm:6.1f}")

    threading.Thread(target=tap_reader, daemon=True).start()
    if verbose:
        print("Beat-Tap-Modus: Enter = Tap im Takt, q = Ende" +
              (f" (Datei: {path})" if path else ""))

    src = None
    q: "queue.Queue | None" = None
    if path:
        src = _make_file_source(path, realtime=True)
        src.ensure_loaded()
        analyzer = Analyzer(samplerate=src.samplerate)
        q = queue.Queue()
        src.start(q)

    last_beat = -1
    try:
        while not stop.is_set():
            if q is not None:
                try:
                    block = q.get(timeout=0.2)
                except queue.Empty:
                    continue
            now = time.monotonic() - t0
            for features in analyzer.process(block):
                st = tracker.update(features, now)
                if st.beat_number != last_beat:
                    last_beat = st.beat_number
                    if verbose:
                        print(f"  beat {st.beat_number:4d}  bpm={st.bpm:6.1f}  phase={st.phase:.2f}"
                              + ("  BAR" if st.is_bar else "") + ("  [TAP]" if now < tracker.manual_until else ""))
            else:
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        if src is not None:
            src.stop()
    if verbose:
        print(f"Ende: bpm={tracker.bpm:.2f}, beats={tracker._beat_number}")
    return {"bpm": tracker.bpm, "beats": tracker._beat_number}
