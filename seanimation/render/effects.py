"""Effekt-Registry + Effekt-Set (ANFORDERUNGEN.md Abschnitt 7, erweitert v0.6.0).

Jeder Effekt bekommt pro Frame Beat-Phase und Beat-Envelope (Abschnitt 3.3.1).

kind:
  - "bg"            nur generativer Hintergrund-Shader
  - "ring"          Hintergrund + starker Beat-Ring-Overlay
  - "clip_*"        Clip (video/image laut clip_kind) als Basis; smooth oder Frame-Step
                    plus Shader-Effekt: wobble / distort (Bass-Warp) / split (RGB-Split)
"""

from __future__ import annotations

EFFECTS_MVP = [
    # generative Hintergründe (bg.frag, u_mode) — Indizes 0-6 bleiben stabil (Tests/Keys)
    {"id": "reactive_bg",  "name": "Bass-Wellen",           "kind": "bg", "mode": 0},
    {"id": "beat_ring",    "name": "Beat-Ring",             "kind": "ring"},
    {"id": "clip_video",   "name": "Video smooth",          "kind": "clip_video",   "clip_kind": "video"},
    {"id": "clip_image",   "name": "Bild Kick-Puls",        "kind": "clip_image",   "clip_kind": "image"},
    {"id": "clip_wobble",  "name": "Video Kugel-Wobble",    "kind": "clip_wobble",  "clip_kind": "video"},
    {"id": "clip_distort", "name": "Video Bass-Warp",       "kind": "clip_distort", "clip_kind": "video"},
    {"id": "clip_split",   "name": "Video RGB-Split",       "kind": "clip_split",   "clip_kind": "video"},
    # neue generative Hintergründe (v0.8.0)
    {"id": "sunburst",     "name": "Sonnenstrahlen",        "kind": "bg", "mode": 1},
    {"id": "tunnel",       "name": "Tunnel-Zoom",           "kind": "bg", "mode": 2},
    {"id": "plasma",       "name": "Plasma",                "kind": "bg", "mode": 3},
    {"id": "kaleido",      "name": "Kaleidoskop",           "kind": "bg", "mode": 4},
    # neue Clip-Effekte (v0.8.0, clip.frag)
    {"id": "clip_glitch",  "name": "Video Glitch-Slices",   "kind": "clip_glitch",  "clip_kind": "video"},
    {"id": "clip_pixel",   "name": "Bild Pixel-Puls",       "kind": "clip_pixel",   "clip_kind": "image"},
    {"id": "clip_invert",  "name": "Bild Invert-Flash",     "kind": "clip_invert",  "clip_kind": "image"},
]


class EffectRegistry:
    def __init__(self, effects=None):
        self._effects = list(effects if effects is not None else EFFECTS_MVP)

    def register(self, effect: dict) -> None:
        self._effects.append(effect)

    def get(self, index: int) -> dict:
        return self._effects[index % len(self._effects)]

    def by_id(self, effect_id: str) -> dict:
        for e in self._effects:
            if e["id"] == effect_id:
                return e
        raise KeyError(effect_id)

    def names(self) -> list[str]:
        return [e["name"] for e in self._effects]

    def __len__(self) -> int:
        return len(self._effects)
