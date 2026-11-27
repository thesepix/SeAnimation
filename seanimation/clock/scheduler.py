"""Scheduler (Abschnitt 3.3.3): plant Ereignisse (Clip-Wechsel,
Effekt-Trigger, Frame-Step) mit Lookahead auf dem Beat-Grid, damit alles
exakt auf Beat-/Taktlinien passiert und nichts ruckelt (A11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class BeatEvent:
    beat_number: int
    is_bar: bool
    time: float       # Audio-/Render-Zeit des Beats in Sekunden
    phase: float      # 0..1 innerhalb des Beats


class Scheduler:
    """Verwaltet das Beat-Grid (BPM + Phase aus BeatTracker) und geplante
    Events; ruft Callbacks präzise auf Beat-/Bar-Grenzen auf."""

    def __init__(self):
        self._beat_callbacks: list[Callable[[BeatEvent], None]] = []
        self._planned: dict[int, list[Callable[[], None]]] = {}

    def on_beat(self, callback: Callable[[BeatEvent], None]) -> None:
        """Callback registrieren, der bei jedem Beat aufgerufen wird."""
        self._beat_callbacks.append(callback)

    def schedule_at_beat(self, beat_number: int, callback: Callable[[], None]) -> None:
        """Callback für einen bestimmten Beat vormerken (z. B. Clip-Wechsel)."""
        # TODO(MVP): Lookahead-Prüfung gegen Beat-Grid; bei Erreichen ausführen.
        raise NotImplementedError

    def tick(self, beat_event: BeatEvent) -> None:
        """Pro Frame aufrufen: fällige geplante Events + Beat-Callbacks auslösen."""
        # TODO(MVP): Events mit beat_number <= aktuell ausführen und entfernen.
        raise NotImplementedError
