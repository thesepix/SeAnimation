"""Renderer (A8–A9, N1): zwei Fenster + GL-Layer-Compositing.

- Preview-Fenster (dekoriert, mit UI: BPM, Beat, Effektliste, Tap-Button)
- Ausgabe-Fenster (randlos, per F vollbild — in OBS als Fensteraufnahme)

Ebenen pro Frame: Basis (generativer Hintergrund-Shader ODER Clip-Textur
mit Frame-Step / Kick-Puls / Kugel-Wobble) + Beat-Ring-Overlay.
Alle Beat-Parameter kommen aus BeatState (phase + envelope, Abschnitt 3.3).

Hinweis: GL-Code kann in der Sandbox nicht ausgeführt werden (keine GPU) —
getestet wird auf dem Win11-Desktop mit der Release-Exe.
"""

from __future__ import annotations

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


class Renderer:
    def __init__(self, state, preview_size=(960, 540), output_size=(1280, 720)):
        """state: AppState (features, beat_state, active_effect, clip_player, ...)."""
        self.state = state
        # Preview zuerst, dann Ausgabe mit geteilter GL-Context (ein moderngl-Kontext)
        self.preview = pyglet.window.Window(
            preview_size[0], preview_size[1], "SeAnimation – Preview", resizable=True
        )
        self.preview.switch_to()
        self.ctx = moderngl.create_context()
        self.output = pyglet.window.Window(
            output_size[0], output_size[1], "SeAnimation – Ausgabe",
            resizable=True, context=self.preview.context,
        )
        try:
            self.output.borderless = True  # randlos für OBS Window Capture / Fullscreen
        except Exception:
            pass

        # GL-Objekte (einmalig, shared context)
        self.vbo = self.ctx.buffer(_FULLSCREEN_TRI.tobytes())
        self.prog_bg = self.ctx.program(vertex_shader=VERT_SHADER, fragment_shader=_load_frag("bg.frag"))
        self.prog_clip = self.ctx.program(vertex_shader=VERT_SHADER, fragment_shader=_load_frag("clip.frag"))
        self.prog_overlay = self.ctx.program(vertex_shader=VERT_SHADER, fragment_shader=_load_frag("overlay.frag"))
        self.vao_bg = self.ctx.simple_vertex_array(self.prog_bg, self.vbo, "in_vert")
        self.vao_clip = self.ctx.simple_vertex_array(self.prog_clip, self.vbo, "in_vert")
        self.vao_overlay = self.ctx.simple_vertex_array(self.prog_overlay, self.vbo, "in_vert")
        self._clip_tex = None
        self._clip_tex_size = None

        # GL-Info loggen (Diagnose, ob der Kontext ans Fenster gebunden ist)
        try:
            info = self.ctx.info
            print(f"  [render] GL-Kontext: {info.get('GL_RENDERER')} | {info.get('GL_VERSION')}")
        except Exception:
            pass
        self._gl_error_printed = False

        # Draw-Handler: push_handlers ist der dokumentierte Weg (pyglet 2.x);
        # preview.on_draw setzt die App selbst (GL + UI zusammen)
        self.output.push_handlers(on_draw=self._on_draw_output)

    def _safe_render_gl(self, win) -> None:
        """_render_gl mit Einmal-Traceback — ein GL-Fehler darf die App nicht killen."""
        try:
            self._render_gl(win)
        except Exception:
            if not self._gl_error_printed:
                import traceback

                traceback.print_exc()
                self._gl_error_printed = True

    # ---------- Fenster-Events ----------
    def _on_draw_preview(self):
        self.preview.switch_to()
        self._safe_render_gl(self.preview)

    def _on_draw_output(self):
        self.output.switch_to()
        self._safe_render_gl(self.output)

    def toggle_fullscreen(self):
        try:
            self.output.fullscreen = not self.output.fullscreen
        except Exception:
            self.output.set_fullscreen(not self.output.fullscreen)

    # ---------- GL-Pipeline ----------
    def _render_gl(self, win) -> None:
        ctx = self.ctx
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
        if kind in ("clip_video", "clip_image", "clip_wobble") and st.clip_player is not None:
            frame = st.clip_player.get_frame(beat_no)  # Frame-Step: Änderung nur auf dem Beat
            self._update_clip_texture(frame)
            prog = self.prog_clip
            _set(prog, "u_tex", 0)
            _set(prog, "u_res", (win.width, win.height))
            _set(prog, "u_time", now)
            _set(prog, "u_beat_phase", phase)
            _set(prog, "u_beat_env", env)
            _set(prog, "u_wobble", 1.0 if kind == "clip_wobble" else 0.0)
            _set(prog, "u_kick", kick)
            _set(prog, "u_pulse", 1.0 if kind == "clip_image" else 0.0)
            self.vao_clip.render(moderngl.TRIANGLES)
        else:
            prog = self.prog_bg
            _set(prog, "u_res", (win.width, win.height))
            _set(prog, "u_time", now)
            _set(prog, "u_beat_phase", phase)
            _set(prog, "u_beat_env", env)
            _set(prog, "u_bass", bass)
            _set(prog, "u_mid", mid)
            _set(prog, "u_high", high)
            _set(prog, "u_kick", kick)
            self.vao_bg.render(moderngl.TRIANGLES)

        # Overlay: Beat-Ring (stärker im "ring"-Effekt)
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE  # additiv
        prog = self.prog_overlay
        _set(prog, "u_res", (win.width, win.height))
        _set(prog, "u_time", now)
        _set(prog, "u_beat_env", env)
        _set(prog, "u_kick", kick)
        _set(prog, "u_strength", 1.6 if kind == "ring" else 0.7)
        self.vao_overlay.render(moderngl.TRIANGLES)
        ctx.disable(moderngl.BLEND)

    def _update_clip_texture(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        if self._clip_tex is None or self._clip_tex_size != (w, h):
            if self._clip_tex is not None:
                self._clip_tex.release()
            self._clip_tex = self.ctx.texture((w, h), 4, frame.tobytes())
            self._clip_tex_size = (w, h)
            self._clip_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        else:
            self._clip_tex.write(frame.tobytes())
        self._clip_tex.use(0)
