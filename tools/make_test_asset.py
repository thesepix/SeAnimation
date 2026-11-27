#!/usr/bin/env python3
"""Generiert das Test-Audio-Asset tests/assets/beat_124bpm.wav.

8 s, 44100 Hz, Stereo, 16-bit PCM — synthetisches Kick+Click-Signal bei
exakt 124 BPM (SynthSource). Wird von tests/test_asset.py genutzt und kann
für --shot / Doku-Screenshots verwendet werden:

    python tools/make_test_asset.py
    python -m seanimation --shot docs/screenshots/effect0.png --file tests/assets/beat_124bpm.wav --effect 0
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    import soundfile as sf

    import sys

    sys.path.insert(0, str(ROOT))
    from seanimation.audio.synth import SynthSource

    out = ROOT / "tests" / "assets" / "beat_124bpm.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sr = 44100
    sig = SynthSource(bpm=124.0, samplerate=sr, duration=8.0, realtime=False).generate()
    stereo = np.ascontiguousarray(np.stack([sig, sig], axis=1))
    sf.write(out, stereo, sr, subtype="PCM_16")
    print(f"geschrieben: {out.relative_to(ROOT)} ({out.stat().st_size} Bytes, {sr} Hz, 8.0 s, 124 BPM)")


if __name__ == "__main__":
    main()
