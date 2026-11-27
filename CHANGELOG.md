# CHANGELOG

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung SemVer.
Tag `vX.Y.Z` ↔ Release-Asset `SeAnimation-X.Y.Z.exe` (gebaut von `release.yml`,
Fallback: Branch `dist-exe` → `bin/`).

## [0.8.0] — unreleased (PR #3, Branch `vibe/handover-1ac69e`)
### Added
- `HANDOVER.md` (Übergabe-Dokument: aktuelle Aufgabe, letzter guter Stand, versucht/gescheitert, offene Punkte, Umgebungsnotizen)
- `CHANGELOG.md` (diese Datei)
- `tools/check.py` — ein Befehl für Syntax + Unit-Tests + Selftest (`python tools/check.py`)
- `tools/make_test_asset.py` + `tests/assets/beat_124bpm.wav` (8 s Synth-Signal, exakt 124 BPM) + `tests/test_asset.py`
- `--shot PFAD_PNG [--frames N] [--effect N] [--size WxH] [--file TRACK] [--bpm X]` — Headless-Render in unsichtbarem Fenster, speichert Frame als PNG (Referenz-Screenshots für Doku/KI; ohne `--file` Synth-Signal)
- Gepinnte `requirements.txt` (getestete Versionen, siehe Header-Kommentar)
### Changed
- `Renderer(..., visible=False, with_output=False)` für unsichtbares Einzelfenster (Shot-Modus)
- README/AGENTS.md: Links auf HANDOVER/CHANGELOG, Check-Befehl, Shot-Modus

## [0.7.1] — 2026-11-27
### Fixed
- Performance-Hotfix: `--file` thread-los (Datei komplett im RAM, Wiedergabe per OutputStream-Callback, Analyse per Wallclock im Render-Loop) — kein Stottern/halbe Geschwindigkeit mehr
- Frame-Limiter ~60 fps pro Fenster
- `PROJEKT.md` (Zusammenfassung für externe KIs)

## [0.7.0] — 2026-11-27
### Added
- Performance: Prefetch-Decode im Hintergrund-Thread, Downscale ≤720p, kein `tobytes`, Upload-Skip bei unverändertem Frame
- GL-GUI: klickbares Thumbnail-Raster der Clips aus `media/` (paginiert), PIL-Text, TAP-Button, Effekte 1–9

## [0.6.0] — 2026-11-27
### Changed
- Bilder/Videos nicht mehr kopfstehend (Y-Flip)
- Video standardmäßig flüssig (Frame-Step optional via `VIDEO_FRAME_STEP`)
- Auto-Wechsel des Clips alle 4 Takte (auf Bar quantisiert)
- `--file` spielt die Datei über die Lautsprecher mit (`PLAY_FILE_AUDIO`)
- 7 Effekte, Tasten 1–9

## [0.5.0] — 2026-11-27
### Changed
- `--file` startet die GUI (CLI-Analyse umgezogen auf `--analyze`)
- Konsolen-Feedback ob Audio/Beat/Pipeline leben
- Loopback via Core Audio bestätigt (`--check-audio` PASS, 44100 Hz)

## [0.4.9] — 2026-11-27
### Fixed
- `device_label`-Fix + `CoInitialize` (pycaw) + `--check-audio` zum isolierten Audio-Test

## [0.4.8] — 2026-11-27
### Fixed
- pycaw `WAVEFORMATEX .contents` Fix (Live-Loopback) + UI-Sichtbarkeit

## [0.4.7] — 2026-11-27
### Fixed
- comtypes-Cast für pycaw `Activate`/`GetService`; GL rendert bestätigt (Screenshot)

## [0.4.6] — 2026-11-27
### Fixed
- eigener GL-Kontext pro Fenster (`Canvas-not-attached`-Crash) + pycaw `_iid_`-Fix für Loopback

## [0.4.5] — 2026-11-27
### Fixed
- pycaw-Import (aktuelles Layout, `IAudioCaptureClient` via comtypes) + pyglet `push_handlers` + GL-Diagnose-Logging

## [0.4.4] — 2026-11-27
### Fixed
- Live-Loopback via pycaw/Core-Audio (PortAudio listet auf Win11 oft keine Loopback-Geräte); GL-Crash im ersten Frame (`u_beat_phase`)

## [0.4.3] — 2026-11-27
### Added
- GUI öffnet auch bei Audio-Fehlern; `--list-devices` / `--device N`; robusteres Loopback-Matching

## [0.4.2] — 2026-11-27
### Fixed
- Live-Loopback nimmt „Was du hörst" der Default-Ausgabe (vorher Mikrofon); `media/` neben der Exe; GUI-Logging

## [0.4.1] — 2026-11-27
### Fixed
- `media/`-Ordner liegt neben der Exe (in der 0.4.0-Exe zeigte MEDIA_DIR ins PyInstaller-Temp)

## [0.4.0] — 2026-11-27
### Added
- Renderer + GUI: zwei Fenster (Preview mit Tap-Button/Effektliste + randloses OBS-Ausgabefenster), 5 MVP-Effekte, Frame-Step-Video, WASAPI-Loopback live

## [0.3.0] — 2026-11-27
### Added
- Versionierter Exe-Name (`SeAnimation-X.Y.Z.exe`) + Beat-Tap (`--tap`) als Fallback bei schlechter Erkennung

## [0.2.0] — 2026-11-27
### Added
- Audio/Beat-Pipeline als standalone Exe: FLAC/MP3/WAV via `--file`, WASAPI-Loopback, Kick-basierter Beat-Snap, Selftest PASS (90–190 BPM)
