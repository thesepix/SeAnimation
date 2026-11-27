"""WavFileSource: stdlib-Fallback für WAV-Dateien, falls soundfile fehlt.

Nur PCM 8/16/24/32 bit (24-bit mit Vorzeichenerweiterung). Bevorzugt wird
AudioFileSource (soundfile) — damit funktionieren auch FLAC/MP3/OGG.
"""

from __future__ import annotations

import wave

import numpy as np

from .file import AudioFileSource


class WavFileSource(AudioFileSource):
    def load(self) -> np.ndarray:
        """WAV via stdlib-wave dekodieren -> float32 (n, channels)."""
        try:
            w = wave.open(str(self.path), "rb")
        except wave.Error as e:
            raise ValueError(
                f"{self.path}: kein lesbares PCM-WAV ({e}). Bitte konvertieren, z. B.: "
                "ffmpeg -i eingabe.wav -c:a pcm_s24le eingabe-24bit.wav"
            ) from e
        with w:
            channels = w.getnchannels()
            sampwidth = w.getsampwidth()
            self.samplerate = w.getframerate()
            raw = w.readframes(w.getnframes())
        if sampwidth == 1:
            data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        elif sampwidth == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 3:
            # 24-bit little-endian -> int32 mit Vorzeichenerweiterung
            b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
            v = (
                b[:, 0].astype(np.int32)
                | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16)
            )
            v = np.where(v & 0x800000, v - 0x1000000, v)
            data = v.astype(np.float32) / 8388608.0
        elif sampwidth == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(
                f"Nicht unterstützte Sample-Breite: {sampwidth} Bytes (nur PCM 8/16/24/32 bit)"
            )
        arr = data.reshape(-1, channels)
        self._data = arr
        return arr
