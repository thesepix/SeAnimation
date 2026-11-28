# SeAnimation

[![CI](https://github.com/thesepix/SeAnimation/actions/workflows/ci.yml/badge.svg)](https://github.com/thesepix/SeAnimation/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/thesepix/SeAnimation?include_prereleases)](https://github.com/thesepix/SeAnimation/releases)

Beat-synchrone Musik-Visuals für **Windows 11** (Python + OpenGL):
Video-/Bild-Clips und generierte Effekte, bei denen jede sichtbare Änderung
**im Takt der Musik** passiert (Frame-Step-Video, Beat-Envelope-Effekte).
Ausgabe im Preview-Fenster oder in einem eigenen randlosen Fenster, das in
**OBS** per Fensteraufnahme eingebunden werden kann.

👉 Das vollständige Anforderungsdokument liegt in **[ANFORDERUNGEN.md](ANFORDERUNGEN.md)**.

## Setup (Win11-Desktop-PC)

Voraussetzungen: Python 3.11+ (64-bit) und ein Audio-Gerät (Default wird
automatisch als WASAPI-Loopback aufgenommen).

```powershell
gh repo clone thesepix/SeAnimation   # privates Repo: gh übernimmt die Auth
cd SeAnimation                       # default branch: main
pip install -r requirements.txt      # oder: pip install -e .
python -m seanimation --selftest        # Beat-Pipeline ohne Audiohardware testen
python -m seanimation --analyze --file <dein-track.flac>   # CLI: Datei durch die Beat-Pipeline
```

`--file` dekodiert via libsndfile: **WAV, FLAC, MP3, OGG** u. a. (`--wav` geht als Alias weiter).

Hinweise:
- In **Windows PowerShell 5.1** gibt es kein `&&` (nur in PowerShell 7 / `pwsh`)
  — Befehle einzeln eingeben oder `;` als Trenner verwenden.
- `python -m seanimation` muss aus dem Repo-Ordner laufen (oder nach `pip install -e .` überall).
- Dateien auch mit absolutem Pfad angebbar, z. B. `--file C:\temp\track.mp3`.

## Schnellstart ohne Python (fertige Exe) — Ziel-PC braucht nichts installiert

Die Windows-Exe wird automatisch per GitHub Actions gebaut (Workflow `ci`,
Job `build-exe`, läuft bei jedem PR und per manuellem Dispatch):

1. PR öffnen → Tab **Actions** → Lauf des PRs → Artifact **`SeAnimation-win64`** laden (enthält `SeAnimation-X.Y.Z.exe`)
2. **Fallback** (wenn das Artifact wegen Account-Quota fehlt): die Exe liegt auf dem
   Branch **`dist-exe`** und lässt sich direkt im Browser laden:
   https://github.com/thesepix/SeAnimation/raw/dist-exe/bin/SeAnimation.exe
3. Testen — **kein Python/git/gh nötig** (aktuell: v0.7.1):
   ```powershell
   .\SeAnimation-0.7.1.exe --selftest
   .\SeAnimation-0.7.1.exe --file <dein-track.flac> (Pfad egal)
   ```

## Exe lokal bauen (einmalig Python 3.11+ von python.org nötig)

```powershell
# Python 3.11+ von python.org installieren, Haken "Add python.exe to PATH" setzen
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
# -> dist\SeAnimation-X.Y.Z.exe (onefile: eine einzige Datei, Version im Namen)
```

## Releases / Versionierung

- SemVer in `seanimation/__init__.py` (`__version__`) und `pyproject.toml`; `SeAnimation-X.Y.Z.exe --version` (SemVer ohne "v"; Tag `vX.Y.Z` ↔ Datei `SeAnimation-X.Y.Z.exe).
- **Der Dateiname trägt die Version**: `SeAnimation-0.7.1.exe` (SemVer aus `__version__`, ohne "v").
- Jeder Release = **annotated Tag `vX.Y.Z`** + GitHub Release (Workflow `release.yml` baut die Exe auf `windows-latest` und hängt sie als Asset an).
- Exe-Download pro Release: Release-Asset `SeAnimation-X.Y.Z.exe` auf GitHub — Fallback (bei Artifact-Quota): Branch **`dist-exe`** →
  - versioniert: https://github.com/thesepix/SeAnimation/raw/dist-exe/bin/SeAnimation-0.7.1.exe
  - immer neueste: https://github.com/thesepix/SeAnimation/raw/dist-exe/bin/SeAnimation.exe
- Changelog: siehe ANFORDERUNGEN.md Abschnitt 10 (Entscheidungsprotokoll) + Release Notes.

## GUI-App (Visuals live)

Ohne Argumente startet die App mit **WASAPI-Loopback** (alles, was der PC abspielt)
bzw. mit `--file` eine Datei in Echtzeit:

```powershell
.\SeAnimation-0.7.1.exe                 # live: Musik auf dem PC abspielen (z. B. Traktor-Ziel später)
.\SeAnimation-0.7.1.exe --file <dein-track.mp3>
```

- **Preview-Fenster (alles klickbar)**: BPM/Beat-Anzeige, **TAP-Button** (Taste **T**),
  Effektliste (Tasten **1-9, 0** — 14 Effekte, Rest per Space/Klick), **Thumbnail-Raster aller Clips aus `media/`** mit Seiten
  (Klick auf Thumbnail = Clip sofort aktiv, Wechsel quantisiert auf Beat)
- **Ausgabe-Fenster**: randlos, Taste **F** = Vollbild — in OBS als Fensteraufnahme einbinden
- **Space** = nächster Effekt (quantisiert auf Beat), Clip-Wechsel automatisch alle 4 Takte, **ESC** = Ende
- Clips (Bilder/Videos) liegen im Ordner **`media/` neben der Exe** (z. B.
  `C:\Desktop\SeAnimation\media\`) und werden beim Start gescannt

## Entwicklung & Mitwirken

**Ein Befehl vor jedem Commit:** `python tools/check.py` (Syntax + Unit-Tests + Selftest).

**Headless-Screenshot (Render-Test ohne GUI, braucht GPU — auf dem Win11-Desktop):**
```powershell
python -m seanimation --shot docs\screenshots\effect0.png --file tests\assets\beat_124bpm.wav --effect 0
# ohne Datei (Synth-Signal 124 BPM):  python -m seanimation --shot out.png --frames 120
```

- Anforderungsänderungen und Code laufen über **Pull Requests** von `main`
  (Branch-Schema `vibe/<slug>-1ac69e`, Draft-PR zum Review) — Details in
  **[CONTRIBUTING.md](CONTRIBUTING.md)**.
- **KI-Agenten** (Claude, Copilot, …) lesen zuerst **[AGENTS.md](AGENTS.md)**
  mit den verbindlichen Regeln; Übergabe-Status siehe **[HANDOVER.md](HANDOVER.md)**,
  Versionshistorie in **[CHANGELOG.md](CHANGELOG.md)**.
- Issue-Templates (Bug/Feature) und PR-Template liegen unter `.github/`;
  Abhängigkeiten aktualisiert Dependabot automatisch (`.github/dependabot.yml`).
- Projektgerüst: Paket `seanimation/` mit den Modulen `audio`, `analysis`,
  `clock`, `library`, `render`, `ui` (siehe Architektur-Diagramm in
  ANFORDERUNGEN.md, Abschnitt 5).
- Lokale Test-Clips (Bilder/Videos) kommen in den Ordner `media/` und werden
  nicht versioniert (siehe `.gitignore`).

## Lizenz

GPL-3.0 — siehe [LICENSE](LICENSE).
