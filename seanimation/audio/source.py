"""AudioSource-Abstraktion (A2).

Alle Audioeingänge liefern PCM-Blöcke (float32, interleaved) in eine
gemeinsame Queue / einen Ringpuffer.

- MVP: `LoopbackSource` — WASAPI-Loopback ("Was du hörst") über sounddevice.
- Test ohne Hardware: `SynthSource` (synthetisches Klick-Signal),
  `WavFileSource` (WAV-Datei, z. B. `python -m seanimation --wav track.wav`).
- Step 2: `NetworkSource` — Audio-Stream vom Traktor-Laptop (z. B. VBAN/RTP).
"""

from __future__ import annotations

import abc
import queue
from typing import Optional

import numpy as np


class AudioSource(abc.ABC):
    """Abstrakte Audioquelle: liefert PCM-Blöcke in eine Queue."""

    @abc.abstractmethod
    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        """Quelle starten; PCM-Blöcke (float32, Form (n, channels)) in out_queue legen."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Quelle stoppen und Ressourcen freigeben."""


def _norm(s) -> str:
    return " ".join(str(s).lower().split())


def _pick_loopback_device(devices: list[dict], hostapi_index: int, default_output_index: int) -> Optional[int]:
    """WASAPI-Loopback-Gerät zur Default-Ausgabe finden: Loopback-Eintrag hat
    (fast) gleichen Namen wie die Ausgabe. Fallback: erstes Gerät mit 'loopback'."""
    if 0 <= default_output_index < len(devices):
        out = _norm(devices[default_output_index]["name"])
        # 1) exakter Name + WASAPI
        for i, d in enumerate(devices):
            if (
                d.get("max_input_channels", 0) > 0
                and d.get("hostapi") == hostapi_index
                and _norm(d["name"]) == out
            ):
                return i
        # 2) unscharf: Ausgabe-Name ist Teil des Eingabe-Namens
        if out:
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0 and out in _norm(d["name"]):
                    return i
    # 3) Fallback: Name enthält "loopback"
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0 and "loopback" in _norm(d["name"]):
            return i
    return None


def list_all_devices() -> None:
    """Alle Audiogeräte mit Index ausgeben (für --list-devices / --device N)."""
    import sounddevice as sd

    print("Verfügbare Audiogeräte (Index für --device N):")
    try:
        default_in, default_out = sd.default.device
    except Exception:
        default_in, default_out = -1, -1
    for i, d in enumerate(sd.query_devices()):
        mark = ""
        if i == default_in:
            mark += " [default IN]"
        if i == default_out:
            mark += " [default OUT]"
        print(
            f"  [{i:2d}] {d['name']!r}  in={d.get('max_input_channels')} out={d.get('max_output_channels')}"
            f"  hostapi={d.get('hostapi')}  sr={d.get('default_samplerate')}{mark}"
        )


def find_loopback_device(verbose: bool = False) -> Optional[int]:
    """Index des WASAPI-Loopback-Geräts der Default-Ausgabe (None = keins gefunden)."""
    import sounddevice as sd

    devices = list(sd.query_devices())
    hostapi_index = None
    default_out = -1
    try:
        for i, h in enumerate(sd.query_hostapis()):
            if "WASAPI" in h["name"]:
                hostapi_index = i
                default_out = h["default_output_device"]
                break
    except Exception:
        pass
    idx = None
    if hostapi_index is not None:
        idx = _pick_loopback_device(devices, hostapi_index, default_out)
    if idx is None:
        idx = _pick_loopback_device(devices, -1, -1)
    if idx is None and verbose:
        print("  [audio] kein Loopback-Gerät gefunden. Eingabegeräte:")
        for i, d in enumerate(devices):
            if d.get("max_input_channels", 0) > 0:
                print(f"    [{i}] {d['name']!r} hostapi={d.get('hostapi')}")
    return idx


def device_name(device: int) -> str:
    import sounddevice as sd

    return str(sd.query_devices(device)["name"])


def get_default_source(device: Optional[int] = None) -> AudioSource:
    """MVP: WASAPI-Loopback der Default-Ausgabe ('Was du hörst').

    device=None -> Loopback-Gerät der Default-Ausgabe automatisch finden.
    Wirft RuntimeError mit Hinweis, wenn keines existiert (dann 'Stereo Mix'
    aktivieren oder VB-Audio Virtual Cable installieren, oder --file nutzen).
    """
    from .loopback import LoopbackSource

    if device is None:
        device = find_loopback_device(verbose=True)
        if device is None:
            raise RuntimeError(
                "Kein WASAPI-Loopback-Gerät gefunden. Optionen: (1) --list-devices ausführen "
                "und das Loopback-Gerät per --device N wählen, (2) in den Windows-Soundeinstellungen "
                "unter Aufnahme 'Stereo Mix'/'Was du hörst' aktivieren, (3) VB-Audio Virtual Cable "
                "installieren, (4) App mit --file <track> starten."
            )
    return LoopbackSource(device=device)


def list_input_devices() -> list[dict]:
    """Alle Eingangsgeräte auflisten (lazy sounddevice-Import).

    Unter Windows erscheinen Loopback-Geräte als "... (loopback)" im
    WASAPI-Host-API; deren Index kann als `device` an LoopbackSource.
    """
    import sounddevice as sd

    return [
        dict(d, index=i)
        for i, d in enumerate(sd.query_devices())
        if d.get("maxInputChannels", 0) > 0
    ]
