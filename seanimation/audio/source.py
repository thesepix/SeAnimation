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


def _pick_loopback_device(devices: list[dict], hostapi_index: int, default_output_index: int) -> Optional[int]:
    """WASAPI-Loopback-Gerät zur Default-Ausgabe finden (Loopback-Eintrag hat
    denselben Namen wie die Ausgabe); Fallback: erstes Gerät mit 'loopback'."""
    if 0 <= default_output_index < len(devices):
        out_name = devices[default_output_index]["name"]
        for i, d in enumerate(devices):
            if (
                d.get("max_input_channels", 0) > 0
                and d.get("hostapi") == hostapi_index
                and d["name"] == out_name
            ):
                return i
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0 and "loopback" in d["name"].lower():
            return i
    return None


def find_loopback_device() -> Optional[int]:
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
    if hostapi_index is not None:
        idx = _pick_loopback_device(devices, hostapi_index, default_out)
        if idx is not None:
            return idx
    return _pick_loopback_device(devices, -1, -1)


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
        device = find_loopback_device()
        if device is None:
            raise RuntimeError(
                "Kein WASAPI-Loopback-Gerät gefunden. Bitte in den Windows-Soundeinstellungen "
                "unter Aufnahme 'Stereo Mix'/'Was du hörst' aktivieren oder VB-Audio Virtual "
                "Cable installieren — oder die App mit --file <track> starten."
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
