"""GL-UI im Preview-Fenster — komplett über moderngl gezeichnet.

Warum nicht pyglet-2D: pyglet-Labels/Shapes zeichnen auf pyglet-eigenem GL-Context;
nach moderngl-Render sind sie unsichtbar. Deshalb: Text via PIL -> Textur,
Thumbnails als Texturen, alles als texturierte Quads im moderngl-Context.

Maus-Koordinaten (pyglet) sind y-bottom-up wie GL — Hit-Tests direkt kompatibel.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SHADER_DIR = Path(__file__).resolve().parent.parent / "render" / "shaders"


def text_rgba(text: str, size: int = 20, color=(255, 255, 255, 255)) -> np.ndarray:
    """Text via PIL rendern -> RGBA-Array, Y-geflipped für GL."""
    font = None
    for name in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"):
        try:
            font = ImageFont.truetype(name, size)
            break
        except Exception:
            continue
    if font is None:
        try:
            font = ImageFont.load_default(size=size)  # Pillow >= 10.1 mit FreeType
        except TypeError:
            font = ImageFont.load_default()
    dummy = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bbox = dummy.textbbox((0, 0), text, font=font)
    w = max(1, bbox[2] - bbox[0])
    h = max(1, bbox[3] - bbox[1])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((-bbox[0], -bbox[1]), text, font=font, fill=color)
    return np.ascontiguousarray(np.array(img)[::-1])  # Y-Flip


class UI:
    """GL-UI: Header (BPM/Beat, TAP-Button), Effektliste (1-9), Thumbnail-Raster der
    Library-Clips mit Seiten (Klick = Clip aktivieren)."""

    PAGE_COLS = 4
    PAGE_ROWS = 3
    THUMB_W = 118
    THUMB_H = 66
    GRID_X = 300
    GRID_Y = 150  # bottom-up

    def __init__(self, app, renderer):
        self.app = app
        self.renderer = renderer
        self.page = 0
        self._tex_cache: dict = {}   # key -> moderngl texture (pro preview-ctx)
        self._white = None
        self._prog = None
        self._logged = False
        self.items: list[tuple] = []  # (x, y, w, h, tex, tint, action)

    # ---------- Texturen ----------
    def _tex(self, g, key, rgba):
        t = self._tex_cache.get(key)
        if t is None:
            h, w = rgba.shape[:2]
            t = g.ctx.texture((w, h), 4, rgba.tobytes())
            t.filter = (g.ctx.LINEAR, g.ctx.LINEAR) if hasattr(g.ctx, "LINEAR") else None
            import moderngl
            t.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._tex_cache[key] = t
        return t

    def _white_tex(self, g):
        if self._white is None:
            self._white = self._tex(g, "__white", np.ones((1, 1, 4), dtype=np.uint8) * 255)
        return self._white

    def _prog_ui(self, g):
        if self._prog is None:
            import moderngl
            self._prog = g.ctx.program(
                vertex_shader=(SHADER_DIR / "ui.vert").read_text(),
                fragment_shader=(SHADER_DIR / "ui.frag").read_text(),
            )
            self._prog_key = id(g.ctx)
        return self._prog

    # ---------- Layout ----------
    def _build_items(self, w, h):
        import moderngl
        g = self.renderer.gl[self.renderer.preview]
        self.items = []
        st = self.app.state
        bs = st.beat_state
        # Header: BPM/Beat
        bpm_text = f"{bs.bpm:6.1f} BPM  Beat {bs.beat_number}" + ("  BAR" if bs and bs.is_bar else "") if bs else "... warte auf Audio"
        if getattr(st, "audio_error", None):
            bpm_text = "AUDIO-FEHLER (siehe Konsole)"
        tex = self._tex(g, "bpm:" + bpm_text, text_rgba(bpm_text, 22, (140, 255, 140, 255)))
        self.items.append((10, h - 34, tex.width, tex.height, tex, (1, 1, 1, 1), None))
        # TAP-Button
        bw, bh = 120, 36
        bx, by = w - bw - 10, h - bh - 10
        self.items.append((bx, by, bw, bh, self._white_tex(g), (0.75, 0.2, 0.2, 0.9), ("tap",)))
        ttex = self._tex(g, "tap", text_rgba("TAP (T)", 18, (255, 255, 255, 255)))
        self.items.append((bx + 22, by + 8, ttex.width, ttex.height, ttex, (1, 1, 1, 1), ("tap",)))
        # Beat-Puls-Quadrat
        env = bs.envelope(st.last_time) if bs else 0.0
        s = int(16 + 30 * env)
        self.items.append((w - 60 - s // 2, h - 90 - s // 2, s, s, self._white_tex(g), (1.0, 0.8, 0.25, 0.9), None))
        # Effektliste (1-9)
        active_id = (st.active_effect or {}).get("id")
        for i in range(len(self.app.effects)):
            eff = self.app.effects.get(i)
            mark = ">> " if eff["id"] == active_id else f"{i + 1}. "
            txt = mark + eff["name"]
            tex = self._tex(g, "eff:" + txt, text_rgba(txt, 15, (255, 255, 120, 255) if eff["id"] == active_id else (220, 220, 220, 255)))
            y = h - 80 - i * 26
            self.items.append((10, y, 280, 22, self._white_tex(g), (0.1, 0.1, 0.15, 0.6), ("effect", i)))
            self.items.append((12, y + 3, tex.width, tex.height, tex, (1, 1, 1, 1), ("effect", i)))
        # Thumbnail-Raster (gepaginated)
        clips = self.app.library.clips
        per_page = self.PAGE_COLS * self.PAGE_ROWS
        max_page = max(0, (len(clips) - 1) // per_page) if clips else 0
        self.page = min(max(0, self.page), max_page)
        page_clips = clips[self.page * per_page : (self.page + 1) * per_page]
        active_path = str(st.clip_path) if getattr(st, "clip_path", None) else None
        for idx, clip in enumerate(page_clips):
            col = idx % self.PAGE_COLS
            row = idx // self.PAGE_COLS
            x = self.GRID_X + col * (self.THUMB_W + 6)
            y = self.GRID_Y + (self.PAGE_ROWS - 1 - row) * (self.THUMB_H + 6)
            key = "thumb:" + str(clip.path)
            tex = self._tex(g, key, np.ascontiguousarray(clip.thumbnail[::-1]) if clip.thumbnail is not None else np.zeros((66, 118, 4), np.uint8))
            border = (1.0, 0.85, 0.2, 1.0) if active_path == str(clip.path) else (0.4, 0.4, 0.5, 0.9)
            self.items.append((x - 2, y - 2, self.THUMB_W + 4, self.THUMB_H + 4, self._white_tex(g), border, None))
            self.items.append((x, y, self.THUMB_W, self.THUMB_H, tex, (1, 1, 1, 1), ("clip", clip)))
        # Seiten-Buttons
        if max_page > 0:
            for label, delta in (("< prev", -1), ("next >", +1)):
                tex = self._tex(g, "page:" + label + str(delta), text_rgba(label, 16, (200, 200, 255, 255)))
                x = self.GRID_X + (0 if delta < 0 else 200)
                self.items.append((x, self.GRID_Y - 30, tex.width + 12, tex.height + 8, self._white_tex(g), (0.15, 0.15, 0.25, 0.8), ("page", delta)))
                self.items.append((x + 6, self.GRID_Y - 26, tex.width, tex.height, tex, (1, 1, 1, 1), ("page", delta)))
        # Hinweiszeile
        hint = "1-9 Effekt | Space nächster | T Tap | F Fullscreen | ESC Ende | Klick: Clip"
        tex = self._tex(g, "hint", text_rgba(hint, 12, (150, 150, 150, 255)))
        self.items.append((10, 10, tex.width, tex.height, tex, (1, 1, 1, 1), None))

    # ---------- Zeichnen ----------
    def draw(self, g, w, h) -> None:
        import moderngl

        self._build_items(w, h)
        if not self._logged:
            print(f"  [ui] GL-UI zeichnet {len(self.items)} Elemente")
            self._logged = True
        prog = self._prog_ui(g)
        verts = []
        for (x, y, qw, qh, _tex, _tint, _act) in self.items:
            verts += [
                (x, y, 0.0, 0.0), (x + qw, y, 1.0, 0.0), (x + qw, y + qh, 1.0, 1.0),
                (x, y, 0.0, 0.0), (x + qw, y + qh, 1.0, 1.0), (x, y + qh, 0.0, 1.0),
            ]
        vbo = g.ctx.buffer(np.array(verts, dtype="f4").tobytes())
        vao = g.ctx.vertex_array(prog, [(vbo, "2f 2f", "in_pos", "in_uv")])
        ctx = g.ctx
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        prog["u_res"] = (w, h)
        for i, (x, y, qw, qh, tex, tint, _act) in enumerate(self.items):
            tex.use(0)
            prog["u_tex"] = 0
            prog["u_tint"] = tint
            vao.render(moderngl.TRIANGLES, vertices=6, first=i * 6)
        ctx.disable(moderngl.BLEND)
        vbo.release()
        vao.release()

    # ---------- Hit-Test ----------
    def hit(self, x, y):
        for (ix, iy, iw, ih, _t, _c, action) in reversed(self.items):
            if action and ix <= x <= ix + iw and iy <= y <= iy + ih:
                return action
        return None
