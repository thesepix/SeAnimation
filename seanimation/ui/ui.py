"""UI (A5, A8, A10): nur Maus/Tastatur.

Preview-Fenster zeigt das Thumbnail-Raster der Animations-Bibliothek
(Klick = aktivieren), Effekt-Buttons und BPM-/Beat-Anzeige.

Hotkeys (MVP): Leertaste = nächste Animation, Pfeiltasten = Auswahl im
Raster, F = Ausgabefenster Vollbild umschalten, ESC = Ende.
"""

from __future__ import annotations


class UI:
    def __init__(self, library, effect_registry, scheduler):
        self.library = library
        self.effects = effect_registry
        self.scheduler = scheduler

    def build(self) -> None:
        """Thumbnail-Raster + Buttons aufbauen (moderngl-window / imgui)."""
        # TODO(MVP): Thumbnails aus library.clips als klickbare Kacheln;
        # BPM-/Beat-Anzeige; Hotkey-Binding (siehe Docstring).
        raise NotImplementedError

    def handle_event(self, event) -> bool:
        """Maus-/Tastatur-Event; True = Event verbraucht."""
        # TODO(MVP): Klick auf Thumbnail -> Clip aktivieren (quantisiert auf
        # Beat via Scheduler), Hotkeys umsetzen.
        raise NotImplementedError
