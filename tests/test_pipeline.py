"""Unit-Tests für die Beat-Pipeline (laufen headless, ohne Audiohardware/GPU).

Aufruf: python -m unittest discover -s tests -v
"""

import os
import queue
import tempfile
import unittest
import wave

import numpy as np

from seanimation.analysis.analyzer import Analyzer
from seanimation.analysis.beat import BeatTracker
from seanimation.audio.synth import SynthSource
from seanimation.audio.wavfile import WavFileSource
from seanimation.devtest import run_selftest

try:
    import soundfile as sf
    from seanimation.audio.file import AudioFileSource
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False


def run_pipeline(bpm: float, duration: float, samplerate: int = 48000):
    """Synth-Signal -> Analyzer -> BeatTracker; liefert (tracker, letzter BeatState)."""
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
    return tracker, last_state


class TestAnalyzer(unittest.TestCase):
    def test_band_energies_and_onset(self):
        sr = 48000
        synth = SynthSource(bpm=120.0, samplerate=sr, duration=2.0, realtime=False)
        sig = synth.generate()
        analyzer = Analyzer(samplerate=sr)
        frames = []
        for i in range(0, sig.size, 512):
            frames.extend(analyzer.process(sig[i : i + 512]))
        self.assertGreater(len(frames), 100)
        # Kick/Click erzeugen deutliche Onsets
        self.assertTrue(any(f["onset"] > 0.01 for f in frames))
        # Kick-Energie sitzt im Bassband
        self.assertGreater(max(f["bass"] for f in frames), max(f["high"] for f in frames))
        # Zeitstempel der Frames stimmen mit hop/samplerate
        self.assertAlmostEqual(frames[1]["time"] - frames[0]["time"], 512 / sr, places=6)


class TestBeatTracker(unittest.TestCase):
    def test_bpm_124(self):
        tracker, state = run_pipeline(bpm=124.0, duration=8.0)
        self.assertAlmostEqual(tracker.bpm, 124.0, delta=3.0)
        self.assertIsNotNone(state)
        self.assertGreater(state.beat_number, 10)
        self.assertGreaterEqual(state.phase, 0.0)
        self.assertLessEqual(state.phase, 1.0)

    def test_bpm_90(self):
        tracker, _ = run_pipeline(bpm=90.0, duration=8.0)
        self.assertAlmostEqual(tracker.bpm, 90.0, delta=3.0)

    def test_phase_alignment(self):
        bpm, duration = 128.0, 8.0
        tracker, state = run_pipeline(bpm=bpm, duration=duration)
        true_beats = np.arange(0.0, duration, 60.0 / bpm)
        dist = float(np.min(np.abs(state.time_of_last_beat - true_beats)))
        self.assertLessEqual(dist, 0.3 * (60.0 / bpm))

    def test_no_double_count_with_offbeats(self):
        # Regression: Offbeat-Onsets (8tel) dürfen beat_number nicht aufblähen
        bpm, duration = 124.0, 8.0
        synth = SynthSource(bpm=bpm, samplerate=48000, duration=duration,
                            realtime=False, offbeat=True)
        sig = synth.generate()
        analyzer = Analyzer(samplerate=48000)
        tracker = BeatTracker(samplerate=48000)
        n = 0
        for i in range(0, sig.size, 512):
            for f in analyzer.process(sig[i : i + 512]):
                n = tracker.update(f, f["time"]).beat_number
        expected = duration * bpm / 60.0  # ~16,5 Beats
        self.assertAlmostEqual(n, expected, delta=expected * 0.25)
        self.assertAlmostEqual(tracker.bpm, bpm, delta=3.0)

    def test_envelope(self):
        tracker, state = run_pipeline(bpm=120.0, duration=4.0)
        # Direkt auf dem Beat ~1, kurz vor dem nächsten Beat klein
        env_on = state.envelope(state.time_of_last_beat + 0.001)
        env_late = state.envelope(state.time_of_last_beat + 0.9 * tracker.period)
        self.assertGreater(env_on, 0.95)
        self.assertLess(env_late, env_on)


class TestSelftest(unittest.TestCase):
    def test_selftest_pass(self):
        self.assertTrue(run_selftest(bpm=124.0, duration=8.0, verbose=False))


class TestWavFileSource(unittest.TestCase):
    def test_load_pcm16(self):
        sr = 44100
        t = np.arange(sr // 2) / sr
        pcm = (0.5 * np.sin(2 * np.pi * 440.0 * t) * 32767).astype(np.int16)
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr)
                w.writeframes(pcm.tobytes())
            src = WavFileSource(path)
            arr = src.load()
            self.assertEqual(arr.shape, (sr // 2, 1))
            self.assertEqual(src.samplerate, sr)
            self.assertLessEqual(float(np.abs(arr).max()), 1.0)
            self.assertGreater(float(np.abs(arr).max()), 0.4)  # Signal nicht leer
        finally:
            os.unlink(path)

    def test_load_pcm24(self):
        # 24-bit-PCM-WAV (wie z. B. AnnaPainting.wav) muss dekodiert werden,
        # inkl. Vorzeichenerweiterung bei negativen Samples.
        sr = 44100
        t = np.arange(sr // 2) / sr
        x = 0.5 * np.sin(2 * np.pi * 440.0 * t)  # enthält negative Werte
        v = np.round(x * 8388607.0).astype(np.int32)
        u = (v & 0xFFFFFF).astype(np.uint32)
        b = np.stack(
            [
                (u & 0xFF).astype(np.uint8),
                ((u >> 8) & 0xFF).astype(np.uint8),
                ((u >> 16) & 0xFF).astype(np.uint8),
            ],
            axis=1,
        )
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(3)
                w.setframerate(sr)
                w.writeframes(b.reshape(-1).tobytes())
            src = WavFileSource(path)
            arr = src.load()
            self.assertEqual(arr.shape, (sr // 2, 1))
            self.assertEqual(src.samplerate, sr)
            self.assertTrue(np.allclose(arr[:, 0], x, atol=1e-5))
        finally:
            os.unlink(path)


class TestBeatTap(unittest.TestCase):
    def test_tap_sets_tempo_and_phase(self):
        tr = BeatTracker(samplerate=48000)
        period = 60.0 / 120.0
        t0 = 1.0
        state = None
        for i in range(6):
            tr.tap(t0 + i * period)
            state = tr.update({"onset": 0.0, "kick": 0.0}, t0 + i * period + 0.01)
        self.assertAlmostEqual(tr.bpm, 120.0, delta=2.0)
        self.assertGreater(state.beat_number, 3)
        # Phase direkt nach dem Tap ~0
        self.assertLess(state.phase, 0.2)

    def test_tap_overrides_detection(self):
        # Synth läuft mit 124 BPM, User tappt aber 100 BPM -> im Manual-Modus gewinnt der Tap
        sig = SynthSource(bpm=124.0, samplerate=48000, duration=6.0, realtime=False).generate()
        analyzer = Analyzer(samplerate=48000)
        tracker = BeatTracker(samplerate=48000)
        taps = [1.0 + i * 0.6 for i in range(9)]  # 100 BPM
        ti = 0
        for i in range(0, sig.size, 512):
            for f in analyzer.process(sig[i : i + 512]):
                now = f["time"]
                if ti < len(taps) and now >= taps[ti]:
                    tracker.tap(now)
                    ti += 1
                tracker.update(f, now)
        self.assertAlmostEqual(tracker.bpm, 100.0, delta=5.0)

    def test_detection_resumes_after_tap_timeout(self):
        # Nach 8 s ohne Tap übernimmt die Erkennung wieder
        tr = BeatTracker(samplerate=48000)
        tr.tap(1.0)
        tr.tap(1.5)  # 120 BPM manuell
        self.assertAlmostEqual(tr.bpm, 120.0, delta=2.0)
        # nach manual_until: synthetische Onsets bei 150 BPM (Ruhe dazwischen,
        # damit der adaptive Schwellwert greift)
        period = 60.0 / 150.0
        t = 20.0
        last_spike = t
        for i in range(12):
            for _ in range(6):  # Ruhe-Frames, damit der adaptive Schwellwert greift
                t += 0.01
                tr.update({"onset": 0.0, "kick": 0.0}, t)
            t = last_spike + period  # Spike exakt im 150-BPM-Abstand
            tr.update({"onset": 1.0, "kick": 1.0}, t)
            last_spike = t
        self.assertAlmostEqual(tr.bpm, 150.0, delta=8.0)


class TestLoopbackDevicePick(unittest.TestCase):
    def test_pick_loopback_by_output_name(self):
        from seanimation.audio.source import _pick_loopback_device

        devices = [
            {"name": "Mikrofon (Realtek)", "max_input_channels": 2, "hostapi": 0},
            {"name": "Speakers (Realtek)", "max_input_channels": 0, "hostapi": 0},   # output
            {"name": "Speakers (Realtek)", "max_input_channels": 2, "hostapi": 0},   # loopback
            {"name": "Other (loopback)", "max_input_channels": 2, "hostapi": 0},
        ]
        # Default-Ausgabe = Index 1 -> Loopback mit gleichem Namen = Index 2
        self.assertEqual(_pick_loopback_device(devices, hostapi_index=0, default_output_index=1), 2)

    def test_pick_loopback_fallback_by_name(self):
        from seanimation.audio.source import _pick_loopback_device

        devices = [
            {"name": "Mikrofon", "max_input_channels": 2, "hostapi": 0},
            {"name": "Höhen (loopback)", "max_input_channels": 2, "hostapi": 0},
        ]
        self.assertEqual(_pick_loopback_device(devices, hostapi_index=-1, default_output_index=-1), 1)
        self.assertIsNone(_pick_loopback_device([{"name": "Mikrofon", "max_input_channels": 2, "hostapi": 0}], 0, -1))

    def test_pick_loopback_fuzzy_name(self):
        from seanimation.audio.source import _pick_loopback_device

        devices = [
            {"name": "Mikrofon (Realtek)", "max_input_channels": 2, "hostapi": 1},
            {"name": "Speakers (Realtek HD Audio)", "max_input_channels": 0, "hostapi": 1},  # output
            {"name": "Speakers (Realtek HD Audio) (loopback)", "max_input_channels": 2, "hostapi": 1},
        ]
        # unscharfer Match: Ausgabe-Name ist Teil des Loopback-Namens
        self.assertEqual(_pick_loopback_device(devices, hostapi_index=1, default_output_index=1), 2)


@unittest.skipUnless(HAS_SOUNDFILE, "soundfile nicht installiert")
class TestAudioFileSource(unittest.TestCase):
    def test_load_flac(self):
        # FLAC-Roundtrip: über soundfile schreiben und lesen (Format wie die
        # echten Test-Files des Users: FLAC/MP3 statt WAV)
        sr = 44100
        t = np.arange(sr // 2) / sr
        x = 0.5 * np.sin(2 * np.pi * 440.0 * t)
        fd, path = tempfile.mkstemp(suffix=".flac")
        os.close(fd)
        try:
            sf.write(path, x.astype(np.float32), sr, format="FLAC")
            src = AudioFileSource(path)
            arr = src.load()
            self.assertEqual(arr.shape, (sr // 2, 1))
            self.assertEqual(src.samplerate, sr)
            self.assertTrue(np.allclose(arr[:, 0], x, atol=1e-4))
        finally:
            os.unlink(path)

    def test_unsupported_format_raises(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.write(fd, b"kein audio")
        os.close(fd)
        try:
            with self.assertRaises(Exception):
                AudioFileSource(path).load()
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
