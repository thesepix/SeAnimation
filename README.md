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
python -m seanimation --selftest      # Beat-Pipeline ohne Audiohardware testen
python -m seanimation --wav C:\temp\AnnaPainting.wav   # WAV-Datei durch die Pipeline
```

Hinweise:
- In **Windows PowerShell 5.1** gibt es kein `&&` (nur in PowerShell 7 / `pwsh`)
  — Befehle einzeln eingeben oder `;` als Trenner verwenden.
- `python -m seanimation` muss aus dem Repo-Ordner laufen (oder nach `pip install -e .` überall).
- WAV-Dateien auch mit absolutem Pfad angebbar, z. B. `--wav C:\temp\AnnaPainting.wav`.

## Schnellstart ohne Python (fertige Exe) — Ziel-PC braucht nichts installiert

Die Windows-Exe wird automatisch per GitHub Actions gebaut (Workflow `ci`,
Job `build-exe`, Läuft bei jedem Push/PR):

1. PR öffnen → Tab **Actions** → Lauf des Branches `vibe/anforderungen-1ac69e`
   → Artifact **`SeAnimation-win64`** herunterladen (enthält die einzelne Datei `SeAnimation.exe`)
2. Entpacken und testen — **kein Python/git/gh nötig**:
   ```powershell
   .\SeAnimation.exe --selftest
   .\SeAnimation.exe --wav C:\temp\AnnaPainting.wav
   ```

## Exe lokal bauen (einmalig Python 3.11+ von python.org nötig)

```powershell
# Python 3.11+ von python.org installieren, Haken "Add python.exe to PATH" setzen
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
# -> dist\SeAnimation.exe (onefile: eine einzige Datei)
```

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
