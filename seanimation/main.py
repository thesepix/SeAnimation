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
    parser.add_argument(
        "--tap",
        action="store_true",
        help="Beat-Tap-Modus: Enter tappt den Beat (überschreibt die Erkennung für 8 s), q = Ende",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Alle Audiogeräte mit Index auflisten (für --device N) und beenden",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        metavar="N",
        help="Audiogerät-Index aus --list-devices statt automatischem Loopback wählen",
    )
    args = parser.parse_args()

    if args.list_devices:
        from .audio.source import list_all_devices

        list_all_devices()
        return

    if args.tap:
        from .devtest import run_tap_mode

        run_tap_mode(args.audio_file)
        return

    if args.selftest:
        from .devtest import run_selftest

        ok = run_selftest(bpm=args.bpm)
        raise SystemExit(0 if ok else 1)

    if args.audio_file and not args.tap:
        from .devtest import run_file_analysis

        result = run_file_analysis(args.audio_file)
        raise SystemExit(0 if result["beats"] else 1)

    # Default: GUI-App (Loopback live oder --file in Echtzeit)
    from . import config

    print(f"SeAnimation {__version__} – starte GUI "
          f"(Audio: {'Datei ' + args.audio_file if args.audio_file else 'WASAPI-Loopback (Was du hörst)'})")
    print(f"Medien-Ordner: {config.MEDIA_DIR}")
    print("Tasten: 1-5 Effekt | Space nächster | T Tap | F Fullscreen | ESC Ende")
    from .app import run_app

    try:
        run_app(
            media_dir=config.MEDIA_DIR,
            audio_file=args.audio_file,
            device=args.device if args.device is not None else config.AUDIO_DEVICE,
        )
    except KeyboardInterrupt:
        print("\nBeendet.")
    except Exception:
        import traceback

        traceback.print_exc()
        print("GUI-Fehler — bitte Traceback melden. CLI-Modi: --selftest | --file <track> | --tap")
    # TODO(MVP): Quelle wählen (Loopback/WAV), Queue befüllen, Analyzer +
    # BeatTracker in Schleife, Scheduler initialisieren, Renderer mit
    # Preview- und Ausgabefenster öffnen, UI verdrahten, Event-Loop starten.


if __name__ == "__main__":
    main()
