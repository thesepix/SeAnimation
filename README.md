# SeAnimation

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
cd SeAnimation
git checkout vibe/anforderungen-1ac69e
pip install -r requirements.txt      # oder: pip install -e .
python -m seanimation --selftest        # Beat-Pipeline ohne Audiohardware testen
python -m seanimation --file C:\temp\AnnaPainting.flac   # Audio-Datei durch die Pipeline
```

`--file` dekodiert via libsndfile: **WAV, FLAC, MP3, OGG** u. a. (`--wav` geht als Alias weiter).

Hinweise:
- In **Windows PowerShell 5.1** gibt es kein `&&` (nur in PowerShell 7 / `pwsh`)
  — Befehle einzeln eingeben oder `;` als Trenner verwenden.
- `python -m seanimation` muss aus dem Repo-Ordner laufen (oder nach `pip install -e .` überall).
- Dateien auch mit absolutem Pfad angebbar, z. B. `--file C:\temp\track.mp3`.

## Schnellstart ohne Python (fertige Exe) — Ziel-PC braucht nichts installiert

Die Windows-Exe wird automatisch per GitHub Actions gebaut (Workflow `ci`,
Job `build-exe`, Läuft bei jedem Push/PR):

1. PR öffnen → Tab **Actions** → Lauf des PRs → Artifact **`SeAnimation-win64`** laden (enthält `SeAnimation.exe`)
2. **Fallback** (wenn das Artifact wegen Account-Quota fehlt): die Exe liegt auf dem
   Branch **`dist-exe`** und lässt sich direkt im Browser laden:
   https://github.com/thesepix/SeAnimation/raw/dist-exe/bin/SeAnimation.exe
3. Testen — **kein Python/git/gh nötig**:
   ```powershell
   .\SeAnimation-v0.3.0.exe --selftest
   .\SeAnimation-v0.3.0.exe --file C:\temp\AnnaPainting.flac
   ```

## Exe lokal bauen (einmalig Python 3.11+ von python.org nötig)

```powershell
# Python 3.11+ von python.org installieren, Haken "Add python.exe to PATH" setzen
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
# -> dist\SeAnimation-vX.Y.Z.exe (onefile: eine einzige Datei, Version im Namen)
```

## Releases / Versionierung

- SemVer in `seanimation/__init__.py` (`__version__`) und `pyproject.toml`; `SeAnimation-vX.Y.Z.exe --version`.
- **Der Dateiname trägt die Version**: `SeAnimation-v0.3.0.exe` (kommt aus der PyInstaller-Spec).
- Jeder Release = **annotated Tag `vX.Y.Z`** + GitHub Release (Workflow `release.yml` baut die Exe auf `windows-latest` und hängt sie als Asset an).
- Exe-Download pro Release: Release-Asset `SeAnimation-vX.Y.Z.exe` auf GitHub — Fallback (bei Artifact-Quota): Branch **`dist-exe`** →
  - versioniert: https://github.com/thesepix/SeAnimation/raw/dist-exe/bin/SeAnimation-v0.3.0.exe
  - immer neueste: https://github.com/thesepix/SeAnimation/raw/dist-exe/bin/SeAnimation.exe
- Changelog: siehe ANFORDERUNGEN.md Abschnitt 10 (Entscheidungsprotokoll) + Release Notes.

## Entwicklung

- Anforderungsänderungen und Code laufen über **Pull Requests** in diesem Repo
  (Branch-Schema `vibe/<slug>-1ac69e`, Draft-PR zum Review).
- Projektgerüst: Paket `seanimation/` mit den Modulen `audio`, `analysis`,
  `clock`, `library`, `render`, `ui` (siehe Architektur-Diagramm in
  ANFORDERUNGEN.md, Abschnitt 5).
- Lokale Test-Clips (Bilder/Videos) kommen in den Ordner `media/` und werden
  nicht versioniert (siehe `.gitignore`).

## Lizenz

GPL-3.0 — siehe [LICENSE](LICENSE).
