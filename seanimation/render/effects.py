"""Effekt-Registry + MVP-Set der 5 Test-Animationen (ANFORDERUNGEN.md Abschnitt 7).

Jeder Effekt bekommt pro Frame Beat-Phase und Beat-Envelope (Abschnitt 3.3.1).

kind:
  - "bg"            nur generativer Hintergrund-Shader
  - "ring"          Hintergrund + starker Beat-Ring-Overlay
  - "clip_video"    Video-Clip im Frame-Step (1 Frame pro Beat)
  - "clip_image"    Bild mit Kick-Puls (Scale/Helligkeit auf dem Beat)
  - "clip_wobble"   Video/Bild mit Kugel-Wobble-Shader (wackelt pro Beat)
"""

from __future__ import annotations

EFFECTS_MVP = [
    {"id": "reactive_bg",     "name": "Reaktiver Hintergrund", "kind": "bg"},
    {"id": "beat_ring",       "name": "Beat-Ring",             "kind": "ring"},
    {"id": "video_frame_step","name": "Video Frame-Step",      "kind": "clip_video"},
    {"id": "image_kick_pulse","name": "Bild Kick-Puls",        "kind": "clip_image"},
    {"id": "sphere_wobble",   "name": "Kugel-Wobble",          "kind": "clip_wobble"},
]

# Tastenkürzel: 1..5
EFFECT_KEYS = {i + 1: i for i in range(len(EFFECTS_MVP))}


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
