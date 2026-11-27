"""WasapiLoopbackSource: Loopback-Capture direkt über Windows Core Audio (pycaw).

Fallback, wenn PortAudio/sounddevice keine Loopback-Geräte listet (auf vielen
Win11-Systemen der Fall): nimmt die Default-Render-Endpoint im
AUDCLNT_STREAMFLAGS_LOOPBACK-Modus auf = "Was du hörst".

Nur Windows (pycaw/comtypes, lazy importiert). Start:
    src = WasapiLoopbackSource(); src.start(queue)
"""

from __future__ import annotations

import queue
import threading
import time

import numpy as np

from .source import AudioSource


class WasapiLoopbackSource(AudioSource):
    def __init__(self, buffer_duration_100ns: int = 10_000_000):
        self.buffer_duration_100ns = buffer_duration_100ns  # 1 s in 100-ns-Einheiten
        self.samplerate = 48000
        self.channels = 2
        self.device_label = "Default-Render-Endpoint (pycaw loopback)"
        self._stop = False
        self._thread: threading.Thread | None = None

    def start(self, out_queue: "queue.Queue[np.ndarray]") -> None:
        import ctypes

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import (
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK,
            EDataFlow,
            ERole,
            IAudioCaptureClient,
            IAudioClient,
            AudioUtilities,
        )

        enumerator = AudioUtilities.GetDeviceEnumerator()
        device = enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender, ERole.eMultimedia)
        try:
            self.device_label = str(device.GetFriendlyName())
        except Exception:
            pass
        client = device.Activate(IAudioClient, CLSCTX_ALL, None)
        fmt = client.GetMixFormat()
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
        capture = client.GetService(IAudioCaptureClient)
        client.Start()
        self._stop = False

        def run() -> None:
            while not self._stop:
                try:
                    p_data, n_frames, _flags = capture.GetBuffer()
                except Exception:
                    time.sleep(0.01)
                    continue
                if n_frames == 0 or not p_data:
                    capture.ReleaseBuffer(0)
                    time.sleep(0.005)
                    continue
                addr = ctypes.cast(p_data, ctypes.c_void_p).value
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
