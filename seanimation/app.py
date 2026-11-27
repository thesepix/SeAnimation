"""App: GUI-Modus — verdrahtet Audio -> Analyzer -> BeatTracker -> Renderer/UI.

Default-Modus (ohne CLI-Flags): WASAPI-Loopback live (oder --file in Echtzeit).
Zwei Fenster: Preview (mit UI) + randloses Ausgabefenster (OBS/Fullscreen).

Tasten: 1-5 Effekt (quantisiert auf Beat), Space nächster Effekt, T Tap,
F Fullscreen, ESC Ende. Maus: Tap-Button, Effektliste klicken.
"""

from __future__ import annotations

import queue
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from . import config
from .analysis.analyzer import Analyzer
from .analysis.beat import BeatTracker
from .audio.source import get_default_source
from .library.clip_player import ClipPlayer
from .library.library import Library
from .render.effects import EffectRegistry
from .render.renderer import Renderer
from .ui.ui import UI


class App:
    def __init__(self, media_dir, audio_file=None, device=None):
        self.state = SimpleNamespace(
            features=None,
            beat_state=None,
            last_time=0.0,
            active_effect=None,
            pending_effect_idx=None,
            clip_player=None,
            clip_path=None,
            pending_clip_override=None,  # per Thumbnail-Klick gewählter Clip
            audio_error=None,
            running=True,
        )
        self.media_dir = media_dir
        self.audio_file = audio_file
        self.device = device
        self.library = Library(media_dir)
        self.effects = EffectRegistry()
        self.analyzer: Analyzer | None = None
        self.tracker = BeatTracker(samplerate=config.AUDIO_SAMPLERATE)
        self.source = None
        self.q: "queue.Queue" = queue.Queue()
        self._last_beat = -1
        self._bar_count = 0
        self._audio_seen = False
        self._first_beat_seen = False
        self.renderer: Renderer | None = None
        self.ui: UI | None = None
        self.out_stream = None
        # Datei-Modus (thread-los, alles im RAM):
        self._file_data: "np.ndarray | None" = None
        self._file_sr = 0
        self._file_pos = 0
        self._play_pos = 0
        self._t0 = 0.0

    # ---------- Audio ----------
    def start_audio(self) -> None:
        if self.audio_file:
            # Datei-Modus: komplett in den RAM dekodieren (einmalig), dann
            # thread-los: Wiedergabe über gerätegetriebenen Output-Callback,
            # Analyse im Render-Loop per Wallclock (kein Source-Thread, kein GIL-Kampf)
            import time

            import numpy as np
            import soundfile as sf

            data, sr = sf.read(self.audio_file, dtype="float32", always_2d=True)
            self._file_data = np.ascontiguousarray(data)
            self._file_sr = int(sr)
            self._file_pos = 0
            self._t0 = time.monotonic()
            print(f"  [app] Audio: Datei {self.audio_file} ({len(data) / sr:.1f}s, {sr} Hz) im Speicher")
            if config.PLAY_FILE_AUDIO:
                try:
                    import sounddevice as sd

                    ch = int(data.shape[1])
                    self._play_pos = 0

                    def _cb(outdata, frames, time_info, status):
                        d = self._file_data
                        n = min(frames, len(d) - self._play_pos)
                        if n > 0:
                            outdata[:n] = d[self._play_pos : self._play_pos + n]
                            self._play_pos += n
                        if n < frames:  # Ende -> Loop
                            outdata[n:] = 0
                            self._play_pos = 0

                    self.out_stream = sd.OutputStream(
                        samplerate=sr, channels=ch, blocksize=config.AUDIO_BLOCKSIZE,
                        dtype="float32", latency="low", callback=_cb,
                    )
                    self.out_stream.start()
                    print(f"  [app] Wiedergabe: Datei läuft über die Lautsprecher ({sr} Hz, {ch} ch, Loop)")
                except Exception as e:
                    print(f"  [app] Wiedergabe fehlgeschlagen (Analyse läuft weiter): {e}")
            self.analyzer = Analyzer(samplerate=self._file_sr)
            self.tracker = BeatTracker(samplerate=self._file_sr)
            return
        # Live-Modus: WASAPI-Loopback (Core Audio) — Musik kommt vom externen Player
        self.source = get_default_source(self.device)
        self.source.start(self.q)
        from .audio.source import device_name

        dev = getattr(self.source, "device", None)
        label = device_name(dev) if dev is not None else getattr(self.source, "device_label", "?")
        print(f"  [app] Audio: Loopback '{label}'")
        sr = int(getattr(self.source, "samplerate", 0) or 0) or config.AUDIO_SAMPLERATE
        print(f"  [app] Samplerate: {sr} Hz")
        self.analyzer = Analyzer(samplerate=sr)
        self.tracker = BeatTracker(samplerate=sr)

    def _process_block(self, block) -> None:
        assert self.analyzer is not None
        for f in self.analyzer.process(block):
            if not self._audio_seen:
                print("  [app] Audio läuft — erste Blöcke verarbeitet")
                self._audio_seen = True
            st = self.tracker.update(f, f["time"])
            self.state.features = f
            self.state.beat_state = st
            self.state.last_time = f["time"]
            if st.beat_number != self._last_beat:
                self._last_beat = st.beat_number
                if st.beat_number == 1 and not self._first_beat_seen:
                    print(f"  [app] erster Beat erkannt (bpm≈{st.bpm:.1f})")
                    self._first_beat_seen = True
                self._on_beat(st)

    def update(self, dt: float) -> None:
        """pyglet-Timer: Audio -> Analyzer -> BeatTracker.

        Live-Modus: Queue der Loopback-Quelle drainen.
        Datei-Modus: thread-los aus dem RAM, per Wallclock getaktet.
        """
        if self.analyzer is None:  # Audio-Start fehlgeschlagen -> nur GUI zeigen
            return
        if self._file_data is not None:
            target = int((time.monotonic() - self._t0) * self._file_sr)
            target = min(target, len(self._file_data))
            target = min(target, self._file_pos + int(0.5 * self._file_sr))  # max 0,5 s aufholen
            while self._file_pos < target:
                block = self._file_data[self._file_pos : self._file_pos + config.AUDIO_BLOCKSIZE]
                self._file_pos += len(block)
                self._process_block(block)
            if self._file_pos >= len(self._file_data):  # Loop
                self._file_pos = 0
                self._t0 = time.monotonic()
            return
        while True:
            try:
                block = self.q.get_nowait()
            except queue.Empty:
                break
            self._process_block(block)

    def _on_beat(self, st) -> None:
        """Wechsel quantisiert auf Beat-Grenze (Abschnitt 3.3.3)."""
        if self.state.pending_effect_idx is not None:
            self.state.active_effect = self.effects.get(self.state.pending_effect_idx)
            self.state.pending_effect_idx = None
            print(f"  [app] Effekt aktiv (auf Beat): {self.state.active_effect['name']}")
            self._apply_effect()
        # Auto-Wechsel des Clips alle N Takte (auf Bar quantisiert)
        if st.is_bar:
            self._bar_count += 1
            eff = self.state.active_effect or {}
            if str(eff.get("kind", "")).startswith("clip_") and self._bar_count % config.CLIP_AUTO_BARS == 0:
                self._apply_clip(eff.get("clip_kind", "video"))
                print(f"  [app] Auto-Wechsel Clip (alle {config.CLIP_AUTO_BARS} Bars)")

    def _eff_index(self) -> int:
        active = self.state.active_effect or {}
        for i in range(len(self.effects)):
            if self.effects.get(i)["id"] == active.get("id"):
                return i
        return 0

    def _apply_effect(self) -> None:
        eff = self.state.active_effect or {}
        kind = eff.get("kind", "bg")
        if kind.startswith("clip_"):
            self._apply_clip(eff.get("clip_kind", "video"))
        else:
            self.state.clip_player = None  # reiner Shader-Hintergrund

    def _apply_clip(self, kind: str) -> None:
        clip = self.state.pending_clip_override
        if clip is not None:
            self.state.pending_clip_override = None
        else:
            clip = self.library.next_clip(kind)
        if clip is None:
            print(f"  [app] kein {kind}-Clip in {self.media_dir} — Fallback: Hintergrund")
            self.state.clip_player = None
            return
        # prefetch=True: Decode läuft im Hintergrund-Thread (Default False, damit sync-Tests einen Thread haben)
        self.state.clip_player = ClipPlayer(clip.path, frames_per_beat=config.FRAMES_PER_BEAT, prefetch=True)
        self.state.clip_path = str(clip.path)
        print(f"  [app] Clip: {clip.path.name} ({kind})")

    # ---------- Input ----------
    def on_key_press(self, symbol, modifiers) -> bool:
        import pyglet

        key = pyglet.window.key
        if symbol == key.ESCAPE:
            self.state.running = False
            return True
        if symbol == key.F and self.renderer:
            self.renderer.toggle_fullscreen()
            return True
        if symbol == key.T:
            self.tracker.tap(self.state.last_time)
            print(f"  [TAP] bpm={self.tracker.bpm:.1f}")
            return True
        if symbol == key.SPACE:
            self.state.pending_effect_idx = (self._eff_index() + 1) % len(self.effects)
            return True
        for i in range(9):  # Tasten 1-9
            k = getattr(key, f"_{i + 1}", None)
            if k is not None and symbol == k and i < len(self.effects):
                self.state.pending_effect_idx = i
                return True
        return False

    def on_mouse_press(self, x, y, button, modifiers) -> bool:
        if self.ui is None:
            return False
        action = self.ui.hit(x, y)  # GL-Koordinaten, y bottom-up wie pyglet-Maus
        if not action:
            return False
        kind = action[0]
        if kind == "tap":
            self.tracker.tap(self.state.last_time)
            print(f"  [TAP] bpm={self.tracker.bpm:.1f}")
            return True
        if kind == "effect":
            self.state.pending_effect_idx = action[1]
            return True
        if kind == "clip":
            clip = action[1]
            self.state.pending_clip_override = clip
            for i in range(len(self.effects)):
                if self.effects.get(i)["kind"] == "clip_video":
                    self.state.pending_effect_idx = i
                    break
            print(f"  [app] Clip per Klick gewählt: {clip.path.name} (aktiv auf nächstem Beat)")
            return True
        if kind == "page":
            self.ui.page += action[1]
            return True
        return False

    # ---------- Loop ----------
    def _on_draw_preview(self) -> None:
        # rendert GL + GL-UI (UI zeichnet der Renderer fürs Preview)
        self.renderer._safe_render_gl(self.renderer.preview)

    def run(self) -> None:
        import pyglet

        # media/ neben der Exe anlegen (falls nicht vorhanden) und scannen
        Path(self.media_dir).mkdir(parents=True, exist_ok=True)
        self.library.scan()
        print(f"  [app] Library: {len(self.library.clips)} Clip(s) in {self.media_dir}")

        # Fenster ZUERST öffnen — Audio-Fehler dürfen die GUI nicht verhindern
        self.state.active_effect = self.effects.get(0)
        self._apply_effect()
        self.renderer = Renderer(self.state, config.PREVIEW_SIZE, config.OUTPUT_SIZE)
        self.ui = UI(self, self.renderer)
        self.renderer.ui = self.ui  # Renderer zeichnet UI im Preview
        for w in (self.renderer.preview, self.renderer.output):
            if w is not None:
                w.push_handlers(on_key_press=self.on_key_press, on_mouse_press=self.on_mouse_press)
        # Preview rendert GL + UI in einem Handler (push_handlers = dokumentierter Weg)
        self.renderer.preview.push_handlers(on_draw=self._on_draw_preview)
        print("  [app] Fenster geöffnet (Preview + Ausgabe)")

        try:
            self.start_audio()
        except Exception as e:
            self.state.audio_error = str(e)
            print(f"  [app] AUDIO-FEHLER (GUI läuft trotzdem): {e}")

        pyglet.clock.schedule_interval(self.update, 1.0 / config.TARGET_FPS)

        def _watchdog(dt):
            if not self.state.running:
                pyglet.app.exit()

        pyglet.clock.schedule_interval(_watchdog, 0.1)
        try:
            pyglet.app.run()
        finally:
            if self.source is not None:
                self.source.stop()
            if self.out_stream is not None:
                self.out_stream.stop()
                self.out_stream.close()


def run_app(media_dir, audio_file=None, device=None) -> None:
    App(media_dir, audio_file, device).run()
