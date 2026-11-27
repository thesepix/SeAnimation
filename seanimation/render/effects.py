"""Beat-getriebene Effekte und das MVP-Set der 5 Test-Animationen (Abschnitt 7).

Jeder Effekt erhält pro Frame die Beat-Phase und die Beat-Envelope
(Impuls auf dem Beat, exponentielles Abklingen — Abschnitt 3.3.1), sodass
jede sichtbare Änderung im Takt passiert.
"""

from __future__ import annotations

# MVP: 5 fest eingebaute Test-Animationen
EFFECTS_MVP = [
    "video_frame_step",  # 1. Video im Frame-Step: 1 Frame pro Beat, Loop über N Beats
    "image_kick_pulse",  # 2. Bild wird auf jedem Beat kurz größer + heller
    "sphere_wobble",     # 3. Video/Bild wird zur Kugel geformt, wackelt pro Beat
    "reactive_bg",       # 4. generativer Hintergrund: Bass treibt Wellen, Kick = Blitz
    "beat_ring",         # 5. Vollbild-Ring/Blitz auf jedem Beat, Farbe wechselt pro Takt
]


class EffectRegistry:
    """Registry aller verfügbaren Animationen/Effekte (Thumbnail-Index -> Effekt)."""

    def __init__(self):
        self._effects: dict[str, object] = {}

    def register(self, name: str, effect) -> None:
        # TODO(MVP): Effekt registrieren.
        raise NotImplementedError

    def get(self, name: str):
        # TODO(MVP): Effekt nach Namen (oder Thumbnail-Index) zurückgeben.
        raise NotImplementedError

    def names(self) -> list[str]:
        return list(self._effects)
