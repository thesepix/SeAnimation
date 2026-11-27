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
    {"id": "reactive_bg",  "name": "Reaktiver Hintergrund", "kind": "bg"},
    {"id": "beat_ring",    "name": "Beat-Ring",             "kind": "ring"},
    {"id": "clip_video",   "name": "Video smooth",          "kind": "clip_video",   "clip_kind": "video"},
    {"id": "clip_image",   "name": "Bild Kick-Puls",        "kind": "clip_image",   "clip_kind": "image"},
    {"id": "clip_wobble",  "name": "Kugel-Wobble",          "kind": "clip_wobble",  "clip_kind": "video"},
    {"id": "clip_distort", "name": "Bass-Warp",             "kind": "clip_distort", "clip_kind": "video"},
    {"id": "clip_split",   "name": "RGB-Split",             "kind": "clip_split",   "clip_kind": "video"},
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
