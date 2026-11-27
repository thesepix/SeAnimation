"""App-Einstieg: verdrahtet die Module.

Datenfluss (siehe ANFORDERUNGEN.md Abschnitt 5):
AudioSource -> Ringpuffer -> Analyzer/BeatTracker -> Scheduler
-> Library (aktive Animation) -> Renderer -> Preview- + Ausgabefenster.

MVP-Stand: Gerüst. Die Einzelmodule sind Stubs, die in den folgenden PRs
implementiert werden.
"""

from . import __version__


def main() -> None:
    print(f"SeAnimation {__version__} – Projektgerüst")
    print("Modul-Implementierung folgt in den nächsten PRs.")
    print("Anforderungen: siehe ANFORDERUNGEN.md im Repo-Root.")
    # TODO(MVP): AudioSource starten, Ringpuffer füllen, Analyzer + BeatTracker
    # laufen lassen, Scheduler mit Beat-Grid initialisieren, Renderer mit
    # Preview- und Ausgabefenster öffnen, UI verdrahten, Event-Loop starten.


if __name__ == "__main__":
    main()
