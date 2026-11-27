"""WasapiLoopbackSource: Loopback-Capture direkt über Windows Core Audio.

Fallback, wenn PortAudio/sounddevice keine Loopback-Geräte listet (auf vielen
Win11-Systemen der Fall): Default-Render-Endpoint im AUDCLNT_STREAMFLAGS_LOOPBACK-
Modus aufnehmen = "Was du hörst".

pycaw (aktuelle Version) liefert IAudioClient/AudioUtilities, aber weder
IAudioCaptureClient noch die AUDCLNT_STREAMFLAGS-Konstanten — die definieren wir
hier selbst via comtypes. Nur Windows; alles lazy importiert.
"""

from __future__ import annotations

import queue
import threading
import time

import numpy as np

from .source import AudioSource

# COM-Konstanten (nicht in pycaw als Modulkonstanten vorhanden)
AUDCLNT_SHAREMODE_SHARED = 0
AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000
IAUDIO_CAPTURE_CLIENT_IID = "{C8ADBD64-E71E-48A0-A4DE-185C395CD317}"


class WasapiLoopbackSource(AudioSource):
    def __init__(self, buffer_duration_100ns: int = 10_000_000):
        self.buffer_duration_100ns = buffer_duration_100ns  # 1 s in 100-ns-Einheiten
        self.samplerate = 48000
        self.channels = 2
        self.device_label = "Default-Render-Endpoint (Core-Audio-Loopback)"
        self._stop = False
        self._thread: threading.Thread | None = None

    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        import ctypes
        from ctypes import c_ubyte, c_uint32, c_uint64, c_void_p

        from comtypes import CLSCTX_ALL, COMMETHOD, GUID, HRESULT, IUnknown, POINTER, cast
        from pycaw.api.audioclient import IAudioClient
        from pycaw.constants import EDataFlow, ERole
        from pycaw.utils import AudioUtilities

        class IAudioCaptureClient(IUnknown):
            _iid_ = GUID(IAUDIO_CAPTURE_CLIENT_IID)
            _methods_ = [
                COMMETHOD(
                    [],
                    HRESULT,
                    "GetBuffer",
                    (["out"], POINTER(POINTER(c_ubyte)), "ppData"),
                    (["out"], POINTER(c_uint32), "pNumFramesToRead"),
                    (["out"], POINTER(c_uint32), "pdwFlags"),
                    (["out"], POINTER(c_uint64), "pu64DevicePosition"),
                    (["out"], POINTER(c_uint64), "pu64QPCPosition"),
                ),
                COMMETHOD([], HRESULT, "ReleaseBuffer", (["in"], c_uint32, "NumFramesRead")),
            ]

        enumerator = AudioUtilities.GetDeviceEnumerator()
        device = enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)
        try:
            self.device_label = str(device.GetFriendlyName())
        except Exception:
            pass
        # comtypes: REFIID-Parameter als GUID-Instanz übergeben (Interface._iid_),
        # dann liefert comtypes automatisch den passend typisierten Pointer zurück
        client = device.Activate(IAudioClient._iid_, CLSCTX_ALL, None)
        fmt = client.GetMixFormat()  # POINTER(WAVEFORMATEX)
        self.samplerate = int(fmt.nSamplesPerSec)
        self.channels = int(fmt.nChannels)
        bits = int(fmt.wBitsPerSample)
        block_align = int(fmt.nBlockAlign)
        client.Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            self.buffer_duration_100ns,
            0,
            fmt,
            None,
        )
        capture = client.GetService(IAudioCaptureClient._iid_)
        client.Start()
        self._stop = False

        def run() -> None:
            while not self._stop:
                try:
                    pp_data, n_frames, _flags, _pos, _qpc = capture.GetBuffer()
                except Exception:
                    time.sleep(0.01)
                    continue
                if not n_frames or not pp_data:
                    capture.ReleaseBuffer(0)
                    time.sleep(0.005)
                    continue
                addr = cast(pp_data, c_void_p).value
                raw = ctypes.string_at(addr, n_frames * block_align)
                capture.ReleaseBuffer(n_frames)
                if bits == 32:
                    arr = np.frombuffer(raw, dtype=np.float32)
                elif bits == 16:
                    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                else:
                    arr = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
                out_queue.put(arr.reshape(-1, self.channels).copy())

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop = True
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
