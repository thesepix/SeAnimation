"""Renderer (A8–A9, N1): zwei Fenster + GL-Layer-Compositing.

- Preview-Fenster (dekoriert, mit UI: BPM, Beat, Effektliste, Tap-Button)
- Ausgabe-Fenster (randlos, per F vollbild — in OBS als Fensteraufnahme)

WICHTIG: jedes Fenster bekommt einen EIGENEN GL-Kontext (geteilte pyglet-Contexts
führen zu "Canvas has not been attached" beim switch_to). Programme/VBO/Texturen
werden pro Fenster erzeugt (_WindowGL).

Ebenen pro Frame: Basis (generativer Hintergrund-Shader ODER Clip-Textur mit
Frame-Step / Kick-Puls / Kugel-Wobble) + Beat-Ring-Overlay. Beat-Parameter aus
BeatState (phase + envelope, Abschnitt 3.3).

GL-Code läuft nicht in der Sandbox (keine GPU) — Test auf dem Win11-Desktop.
"""

from __future__ import annotations

import time
from pathlib import Path

import moderngl
import numpy as np
import pyglet

SHADER_DIR = Path(__file__).parent / "shaders"

VERT_SHADER = """
#version 330
in vec2 in_vert;
void main() { gl_Position = vec4(in_vert, 0.0, 1.0); }
"""

_FULLSCREEN_TRI = np.array([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")


def _load_frag(name: str) -> str:
    return (SHADER_DIR / name).read_text(encoding="utf-8")


def _set(prog, name: str, value) -> None:
    """Uniform setzen, falls vorhanden — der GL-Treiber optimiert unbenutzte
    Uniforms weg, dann gäbe es sonst KeyError."""
    try:
        prog[name] = value
    except KeyError:
        pass


class _WindowGL:
    """GL-Ressourcen pro Fenster (eigener Kontext — geteilte Contexts crashen pyglet)."""

    def __init__(self, win):
        win.switch_to()
        self.ctx = moderngl.create_context()
        self.vbo = self.ctx.buffer(_FULLSCREEN_TRI.tobytes())
        self.prog_bg = self.ctx.program(vertex_shader=VERT_SHADER, fragment_shader=_load_frag("bg.frag"))
        self.prog_clip = self.ctx.program(vertex_shader=VERT_SHADER, fragment_shader=_load_frag("clip.frag"))
        self.prog_overlay = self.ctx.program(vertex_shader=VERT_SHADER, fragment_shader=_load_frag("overlay.frag"))
        self.vao_bg = self.ctx.simple_vertex_array(self.prog_bg, self.vbo, "in_vert")
        self.vao_clip = self.ctx.simple_vertex_array(self.prog_clip, self.vbo, "in_vert")
        self.vao_overlay = self.ctx.simple_vertex_array(self.prog_overlay, self.vbo, "in_vert")
        self.clip_tex = None
        self.clip_tex_size = None
        self.clip_seq = -1  # zuletzt hochgeladenes Frame (Upload-Skip bei Bildern)


class Renderer:
    def __init__(self, state, preview_size=(960, 540), output_size=(1280, 720)):
        """state: AppState (features, beat_state, active_effect, clip_player, ...)."""
        self.state = state
        self.preview = pyglet.window.Window(
            preview_size[0], preview_size[1], "SeAnimation – Preview", resizable=True
        )
        self.output = pyglet.window.Window(
            output_size[0], output_size[1], "SeAnimation – Ausgabe", resizable=True
        )
        try:
            self.output.borderless = True  # randlos für OBS Window Capture / Fullscreen
        except Exception:
            pass

        # pro Fenster eigener GL-Kontext + Ressourcen
        self.gl = {self.preview: _WindowGL(self.preview), self.output: _WindowGL(self.output)}
        for name, g in (("preview", self.gl[self.preview]), ("output", self.gl[self.output])):
            try:
                info = g.ctx.info
                print(f"  [render] GL[{name}]: {info.get('GL_RENDERER')} | {info.get('GL_VERSION')}")
            except Exception:
                pass
        self._gl_error_printed = False
        self._last_now = 0.0
        self._last_draw: dict = {}  # Frame-Limiter pro Fenster (~60 fps cap)
        self._min_frame_s = 1.0 / 62.0

        self.ui = None  # wird von der App gesetzt (GL-UI)

        # Draw-Handler: push_handlers ist der dokumentierte Weg (pyglet 2.x);
        # preview.on_draw setzt die App selbst (GL + UI zusammen)
        self.output.push_handlers(on_draw=self._on_draw_output)

    # ---------- Fenster-Events ----------
    def _throttle(self, key: str) -> bool:
        """Frame-Limiter: max. ~60 fps pro Fenster (sonst frisst das Rendering den Event-Loop)."""
        now = time.monotonic()
        if now - self._last_draw.get(key, 0.0) < self._min_frame_s:
            return True
        self._last_draw[key] = now
        return False

    def _on_draw_preview(self):
        if self._throttle("preview"):
            return
        self.preview.switch_to()
        self._safe_render_gl(self.preview)

    def _on_draw_output(self):
        if self._throttle("output"):
            return
        self.output.switch_to()
        self._safe_render_gl(self.output)

    def _safe_render_gl(self, win) -> None:
        """_render_gl mit Einmal-Traceback — ein GL-Fehler darf die App nicht killen."""
        try:
            self._render_gl(win)
        except Exception:
            if not self._gl_error_printed:
                import traceback

                traceback.print_exc()
                self._gl_error_printed = True

    def toggle_fullscreen(self):
        try:
            self.output.fullscreen = not self.output.fullscreen
        except Exception:
            self.output.set_fullscreen(not self.output.fullscreen)

    # ---------- GL-Pipeline ----------
    def _render_gl(self, win) -> None:
        g = self.gl[win]
        ctx = g.ctx
        st = self.state
        ctx.viewport = (0, 0, win.width, win.height)
        ctx.clear(0.02, 0.02, 0.03)

        bs = st.beat_state
        feats = st.features or {}
        now = st.last_time
        env = bs.envelope(now) if bs else 0.0
        phase = bs.phase if bs else 0.0
        beat_no = bs.beat_number if bs else 0
        bass = float(feats.get("bass", 0.0))
        mid = float(feats.get("mid", 0.0))
        high = float(feats.get("high", 0.0))
        kick = float(feats.get("kick", 0.0))

        eff = st.active_effect or {"kind": "bg"}
        kind = eff.get("kind", "bg")

        # Basis-Layer
        cp = st.clip_player if kind.startswith("clip_") else None
        frame = None
        if cp is not None:
            if cp.frames_per_beat > 0:
                frame = cp.get_frame(beat_no)  # Frame-Step (optional)
            else:
                frame = cp.latest_frame()      # Smooth: neuestes Prefetch-Frame
            self._last_now = now
        if frame is not None:
            self._update_clip_texture(g, frame, cp.frame_seq, flip=not cp._flipped)
            prog = g.prog_clip
            _set(prog, "u_tex", 0)
            _set(prog, "u_res", (win.width, win.height))
            _set(prog, "u_time", now)
            _set(prog, "u_beat_phase", phase)
            _set(prog, "u_beat_env", env)
            _set(prog, "u_bass", bass)
            _set(prog, "u_kick", kick)
            _set(prog, "u_wobble", 1.0 if kind == "clip_wobble" else 0.0)
            _set(prog, "u_pulse", 1.0 if kind == "clip_image" else 0.0)
            _set(prog, "u_distort", 1.0 if kind == "clip_distort" else 0.0)
            _set(prog, "u_split", 1.0 if kind == "clip_split" else 0.0)
            g.vao_clip.render(moderngl.TRIANGLES)
        else:
            prog = g.prog_bg
            _set(prog, "u_res", (win.width, win.height))
            _set(prog, "u_time", now)
            _set(prog, "u_beat_phase", phase)
            _set(prog, "u_beat_env", env)
            _set(prog, "u_bass", bass)
            _set(prog, "u_mid", mid)
            _set(prog, "u_high", high)
            _set(prog, "u_kick", kick)
            g.vao_bg.render(moderngl.TRIANGLES)

        # Overlay: Beat-Ring (stärker im "ring"-Effekt)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE  # additiv
        prog = g.prog_overlay
        _set(prog, "u_res", (win.width, win.height))
        _set(prog, "u_time", now)
        _set(prog, "u_beat_env", env)
        _set(prog, "u_kick", kick)
        _set(prog, "u_strength", 1.6 if kind == "ring" else 0.7)
        g.vao_overlay.render(moderngl.TRIANGLES)
        ctx.disable(moderngl.BLEND)

        # UI nur im Preview, und nur wenn Frames da sind (GL-UI über moderngl)
        if win is self.preview and self.ui is not None:
            try:
                self.ui.draw(g, win.width, win.height)
            except Exception:
                if not self._gl_error_printed:
                    import traceback

                    traceback.print_exc()
                    self._gl_error_printed = True

    def _update_clip_texture(self, g: _WindowGL, frame: np.ndarray, seq: int, flip: bool = True) -> None:
        # Y-Flip nur wenn nicht schon im Prefetch-Thread passiert (cv2/PIL top-down, GL bottom-up)
        if flip:
            frame = np.ascontiguousarray(frame[::-1])
        if seq == g.clip_seq:
            g.clip_tex.use(0)
            return  # unverändertes Frame (Bild) nicht erneut hochladen
        h, w = frame.shape[:2]
        if g.clip_tex is None or g.clip_tex_size != (w, h):
            if g.clip_tex is not None:
                g.clip_tex.release()
            g.clip_tex = g.ctx.texture((w, h), 4, frame)  # ndarray direkt, ohne tobytes-Kopie
            g.clip_tex_size = (w, h)
            g.clip_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        else:
            g.clip_tex.write(frame)
        g.clip_seq = seq
        g.clip_tex.use(0)
