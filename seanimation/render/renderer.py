"""Renderer (A8–A9, N1).

GPU-Compositing der Ebenen mit moderngl:
  1. optionaler generativer Hintergrund-Shader (Bass/Beat-getrieben),
  2. die aktive Animation (Video-Frame oder Bild als Textur, ggf. mit
     Beat-Effekt-Shader wie Kugel-Wobble),
  3. Overlay/Post-Effekte (Beat-Ring, Blitz).

Zwei Fenster: Preview (mit UI) + Ausgabe (randlos, Vollbild per Hotkey,
OBS Window Capture). Clips werden vorgepuffert (A11); bei Dekodier-Fehlern
Fallback auf den generativen Hintergrund.
"""

from __future__ import annotations


class Renderer:
    def __init__(self, target_fps: int = 60):
        self.target_fps = target_fps
        self.preview_window = None
        self.output_window = None

    def open_windows(self) -> None:
        """Preview- und Ausgabefenster öffnen (moderngl-window)."""
        # TODO(MVP): moderngl_window.create_window für beide Fenster;
        # Ausgabefenster randlos (decorations=False), Fullscreen per Hotkey.
        raise NotImplementedError

    def render_frame(self, features: dict, beat_state, active_clip) -> None:
        """Ein Frame in beide Fenster rendern.

        features: Analyzer-Features (Bänder, Onset)
        beat_state: BeatState (phase, envelope für Beat-Sync-Modell 3.3)
        active_clip: aktiver Clip (Video-Frame-Step oder Bild + Effekt)
        """
        # TODO(MVP): Video-Frame via OpenCV in Textur laden (Frame-Step laut
        # Beat-Phase), Shader-Parameter aus features/beat_state setzen,
        # Ebenen compositen, in beide Fenster zeichnen.
        raise NotImplementedError
