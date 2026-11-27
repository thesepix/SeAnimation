"""App: GUI-Modus — verdrahtet Audio -> Analyzer -> BeatTracker -> Renderer/UI.

Default-Modus (ohne CLI-Flags): WASAPI-Loopback live (oder --file in Echtzeit).
Zwei Fenster: Preview (mit UI) + randloses Ausgabefenster (OBS/Fullscreen).

Tasten: 1-5 Effekt (quantisiert auf Beat), Space nächster Effekt, T Tap,
F Fullscreen, ESC Ende. Maus: Tap-Button, Effektliste klicken.
"""

from __future__ import annotations

import queue
from pathlib import Path
from types import SimpleNamespace

from . import config
from .analysis.analyzer import Analyzer
from .analysis.beat import BeatTracker
from .audio.source import get_default_source
from .devtest import _make_file_source
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
        self.renderer: Renderer | None = None
        self.ui: UI | None = None

    # ---------- Audio ----------
    def start_audio(self) -> None:
        if self.audio_file:
            self.source = _make_file_source(self.audio_file, realtime=True)
            self.source.ensure_loaded()
            print(f"  [app] Audio: Datei {self.audio_file}")
        else:
            self.source = get_default_source(self.device)  # WASAPI-Loopback der Default-Ausgabe
        self.source.start(self.q)
        if not self.audio_file:
            from .audio.source import device_name

            print(f"  [app] Audio: Loopback '{device_name(self.source.device)}'")
        sr = int(getattr(self.source, "samplerate", 0) or 0) or config.AUDIO_SAMPLERATE
        print(f"  [app] Samplerate: {sr} Hz")
        self.analyzer = Analyzer(samplerate=sr)
        self.tracker = BeatTracker(samplerate=sr)

    def update(self, dt: float) -> None:
        """pyglet-Timer: Audio-Queue drainen -> Analyzer -> BeatTracker."""
        assert self.analyzer is not None
        while True:
            try:
                block = self.q.get_nowait()
            except queue.Empty:
                break
            for f in self.analyzer.process(block):
                st = self.tracker.update(f, f["time"])
                self.state.features = f
                self.state.beat_state = st
                self.state.last_time = f["time"]
                if st.beat_number != self._last_beat:
                    self._last_beat = st.beat_number
                    self._on_beat(st)

    def _on_beat(self, st) -> None:
        """Wechsel quantisiert auf Beat-Grenze (Abschnitt 3.3.3)."""
        if self.state.pending_effect_idx is not None:
            self.state.active_effect = self.effects.get(self.state.pending_effect_idx)
            self.state.pending_effect_idx = None
            self._apply_effect()

    def _eff_index(self) -> int:
        active = self.state.active_effect or {}
        for i in range(len(self.effects)):
            if self.effects.get(i)["id"] == active.get("id"):
                return i
        return 0

    def _apply_effect(self) -> None:
        eff = self.state.active_effect or {}
        kind = eff.get("kind", "bg")
        if kind in ("clip_video", "clip_wobble"):
            self._apply_clip("video")
        elif kind == "clip_image":
            self._apply_clip("image")
        else:
            self.state.clip_player = None  # reiner Shader-Hintergrund

    def _apply_clip(self, kind: str) -> None:
        clip = self.library.next_clip(kind)
        if clip is None:
            print(f"  [app] kein {kind}-Clip in {self.media_dir} — Fallback: Hintergrund")
            self.state.clip_player = None
            return
        self.state.clip_player = ClipPlayer(clip.path, frames_per_beat=config.FRAMES_PER_BEAT)
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
        for num, idx in ((key._1, 0), (key._2, 1), (key._3, 2), (key._4, 3), (key._5, 4)):
            if symbol == num and idx < len(self.effects):
                self.state.pending_effect_idx = idx
                return True
        return False

    def on_mouse_press(self, x, y, button, modifiers) -> bool:
        if self.ui is None:
            return False
        if self.ui.hit_tap(x, y):
            self.tracker.tap(self.state.last_time)
            print(f"  [TAP] bpm={self.tracker.bpm:.1f}")
            return True
        idx = self.ui.hit_effect(x, y)
        if idx is not None:
            self.state.pending_effect_idx = idx
            return True
        return False

    # ---------- Loop ----------
    def _on_draw_preview(self) -> None:
        self.renderer.preview.switch_to()
        self.renderer._render_gl(self.renderer.preview)
        self.ui.draw()  # UI über GL

    def run(self) -> None:
        import pyglet

        # media/ neben der Exe anlegen (falls nicht vorhanden) und scannen
        Path(self.media_dir).mkdir(parents=True, exist_ok=True)
        self.library.scan()
        print(f"  [app] Library: {len(self.library.clips)} Clip(s) in {self.media_dir}")
        self.start_audio()
        self.state.active_effect = self.effects.get(0)
        self._apply_effect()

        self.renderer = Renderer(self.state, config.PREVIEW_SIZE, config.OUTPUT_SIZE)
        self.ui = UI(self, self.renderer.preview)
        for w in (self.renderer.preview, self.renderer.output):
            w.push_handlers(on_key_press=self.on_key_press, on_mouse_press=self.on_mouse_press)
        self.renderer.preview.on_draw = self._on_draw_preview  # GL + UI
        # output.on_draw bleibt Renderer._on_draw_output

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


def run_app(media_dir, audio_file=None, device=None) -> None:
    App(media_dir, audio_file, device).run()
