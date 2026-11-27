"""App-Einstieg: verdrahtet die Module.

Datenfluss (siehe ANFORDERUNGEN.md Abschnitt 5):
AudioSource -> Ringpuffer -> Analyzer/BeatTracker -> Scheduler
-> Library (aktive Animation) -> Renderer -> Preview- + Ausgabefenster.

Bisher implementiert: Audio-Quellen (Loopback/Synth/WAV) + Analyzer +
BeatTracker + Selftest. Renderer/UI folgen in den nächsten PRs.
"""

from __future__ import annotations

import argparse

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="seanimation",
        description="SeAnimation – beat-synchrone Musik-Visuals (Windows 11)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Beat-Pipeline gegen synthetisches Klick-Signal testen (ohne Audiohardware)",
    )
    parser.add_argument(
        "--file",
        "--wav",  # Alias aus Kompatibilitätsgründen
        dest="audio_file",
        metavar="PFAD",
        default=None,
        help="Audio-Datei (WAV/FLAC/MP3/OGG/...) als Quelle statt WASAPI-Loopback",
    )
    parser.add_argument(
        "--bpm",
        type=float,
        default=124.0,
        help="BPM der Synth-Quelle (nur mit --selftest relevant)",
    )
    args = parser.parse_args()

    if args.selftest:
        from .devtest import run_selftest

        ok = run_selftest(bpm=args.bpm)
        raise SystemExit(0 if ok else 1)

    if args.audio_file:
        from .devtest import run_file_analysis

        result = run_file_analysis(args.audio_file)
        raise SystemExit(0 if result["beats"] else 1)

    print(f"SeAnimation {__version__} – Projektgerüst")
    print("Audioquelle: WASAPI-Loopback (Standard-Audiogerät)")
    print("TODO(MVP): Vollständige Pipeline mit Renderer/UI starten.")
    print("Headless-Tests: python -m seanimation --selftest | --file <track.flac/mp3/wav> | Doku: ANFORDERUNGEN.md")
    # TODO(MVP): Quelle wählen (Loopback/WAV), Queue befüllen, Analyzer +
    # BeatTracker in Schleife, Scheduler initialisieren, Renderer mit
    # Preview- und Ausgabefenster öffnen, UI verdrahten, Event-Loop starten.


if __name__ == "__main__":
    main()
