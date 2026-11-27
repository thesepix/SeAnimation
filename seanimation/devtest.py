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


def run_shot(
    out_path,
    audio_file=None,
    frames: int = 120,
    effect_idx: int = 0,
    size=(1280, 720),
    bpm: float = 124.0,
    fps: float = 60.0,
    media_dir=None,
    verbose: bool = True,
) -> bool:
    """Headless-Render: rendert `frames` Frames in ein unsichtbares Fenster und
    speichert das letzte Frame als PNG (z. B. Referenz-Screenshots für Doku/KI).

    Ohne audio_file wird ein Synth-Signal (bpm) verwendet — braucht keine
    Audiohardware, aber eine GPU (Windows-Desktop). Läuft NICHT in der CI-Sandbox.
    """
    from types import SimpleNamespace

    import numpy as np

    from . import config
    from .analysis.analyzer import Analyzer
    from .analysis.beat import BeatTracker
    from .library.clip_player import ClipPlayer
    from .library.library import Library
    from .render.effects import EffectRegistry
    from .render.renderer import Renderer

    if audio_file:
        import soundfile as sf

        data, sr = sf.read(audio_file, dtype="float32", always_2d=True)
        data = np.ascontiguousarray(data)
        src_label = f"Datei {audio_file}"
    else:
        from .audio.synth import SynthSource

        sr = 44100
        sig = SynthSource(bpm=bpm, samplerate=sr, duration=max(8.0, frames / fps + 1.0), realtime=False).generate()
        data = np.ascontiguousarray(np.stack([sig, sig], axis=1))
        src_label = f"Synth {bpm:.1f} BPM"
    if verbose:
        print(f"Shot: {frames} Frames @ {fps:.0f} fps, {size[0]}x{size[1]}, Audio: {src_label}, Effekt #{effect_idx}")

    analyzer = Analyzer(samplerate=sr)
    tracker = BeatTracker(samplerate=sr)
    effects = EffectRegistry()
    state = SimpleNamespace(
        features=None, beat_state=None, last_time=0.0,
        active_effect=effects.get(effect_idx), pending_effect_idx=None,
        clip_player=None, clip_path=None, pending_clip_override=None,
        audio_error=None, running=True,
    )
    eff = state.active_effect
    if str(eff.get("kind", "")).startswith("clip_"):
        lib = Library(media_dir or config.MEDIA_DIR)
        lib.scan()
        clip = lib.next_clip(eff.get("clip_kind", "video"))
        if clip is not None:
            state.clip_player = ClipPlayer(clip.path, frames_per_beat=config.FRAMES_PER_BEAT, prefetch=False)
            if verbose:
                print(f"  [shot] Clip: {clip.path.name}")
        elif verbose:
            print("  [shot] kein Clip in media/ gefunden — nur Shader-Hintergrund")

    renderer = Renderer(state, size, size, visible=False, with_output=False)
    win = renderer.preview
    bs = config.AUDIO_BLOCKSIZE
    pos = 0
    try:
        for i in range(frames):
            target = int((i + 1) / fps * sr)
            while pos < min(target, len(data)):
                block = data[pos : pos + bs]
                pos += len(block)
                for f in analyzer.process(block):
                    st = tracker.update(f, f["time"])
                    state.features = f
                    state.beat_state = st
                    state.last_time = f["time"]
            win.switch_to()
            renderer._render_gl(win)  # direkt, ohne Frame-Limiter/Throttle
        win.switch_to()
        g = renderer.gl[win]
        raw = g.ctx.screen.read(components=3, alignment=1)
        from PIL import Image

        img = Image.frombytes("RGB", (win.width, win.height), raw).transpose(Image.FLIP_TOP_BOTTOM)
        img.save(out_path)
        if verbose:
            print(f"  [shot] BPM erkannt: {tracker.bpm:.1f} | gespeichert: {out_path} ({img.size[0]}x{img.size[1]} PNG)")
        return True
    finally:
        if state.clip_player is not None:
            state.clip_player.close()
        try:
            win.close()
        except Exception:
            pass
