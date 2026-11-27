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


if __name__ == "__main__":
    unittest.main()
