"""Test-Audio-Asset (tests/assets/beat_124bpm.wav): vorhanden, ladbar, 124 BPM erkannt.

Headless-sicher (nur numpy/soundfile). Asset neu erzeugen mit:
    python tools/make_test_asset.py
"""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

ASSET = Path(__file__).resolve().parent / "assets" / "beat_124bpm.wav"


class TestBeatAsset(unittest.TestCase):
    def test_asset_exists_and_loads(self):
        import soundfile as sf

        self.assertTrue(ASSET.is_file(), f"Asset fehlt: {ASSET} — python tools/make_test_asset.py")
        data, sr = sf.read(ASSET, dtype="float32", always_2d=True)
        self.assertEqual(sr, 44100)
        self.assertEqual(data.shape[1], 2)  # Stereo
        self.assertAlmostEqual(len(data) / sr, 8.0, delta=0.1)
        self.assertGreater(float(np.abs(data).max()), 0.3)  # nicht leer/leise

    def test_asset_beat_detection_124bpm(self):
        import soundfile as sf

        from seanimation.analysis.analyzer import Analyzer
        from seanimation.analysis.beat import BeatTracker

        data, sr = sf.read(ASSET, dtype="float32", always_2d=True)
        analyzer = Analyzer(samplerate=sr)
        tracker = BeatTracker(samplerate=sr)
        last_st = None
        for i in range(0, len(data), 512):
            for f in analyzer.process(data[i : i + 512]):
                last_st = tracker.update(f, f["time"])
        self.assertIsNotNone(last_st)
        self.assertGreater(last_st.beat_number, 10)
        self.assertAlmostEqual(tracker.bpm, 124.0, delta=3.0)


if __name__ == "__main__":
    unittest.main()
