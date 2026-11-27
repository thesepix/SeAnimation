# SeAnimation — Projektzusammenfassung (für externe KI/Review)

## Ziel
**SeAnimation** ist eine standalone **Windows-11-Exe** für **beat-synchrone Musik-Visuals**:
Musik läuft (lokal oder vom DJ-Laptop), die Software erkennt den Beat und zeigt dazu
passende Visuals — Clips (Bilder/Videos aus einem Ordner) und generierte Shader-Effekte,
bei denen **jede sichtbare Änderung im Takt** passiert.

## Einsatzziel (Set-up)
- **Traktor-DJ** läuft auf einem **Windows-11-Laptop**.
- **Visuals laufen auf einem zweiten Windows-11-Desktop-PC**, dort läuft auch **OBS** (Streaming).
- MVP: Musik lokal auf dem Desktop (Loopback oder `--file`). **Step 2 (geplant):** Audio vom
  Traktor-Laptop übers Netzwerk (z. B. VBAN/RTP) und/oder Traktor-MIDI/OSC-Clock als exakte Taktquelle.
- Ausgabe: Preview-Fenster mit UI + **randloses Ausgabefenster** (Vollbild per F, in OBS als Fensteraufnahme).

## Kernfunktionen (Stand v0.7.1)
- **Audioeingang:** WASAPI-Loopback "Was du hörst" — zuerst PortAudio, Fallback **Core Audio via pycaw**
  (`AUDCLNT_STREAMFLAGS_LOOPBACK`, weil PortAudio auf vielen Win11-PCs keine Loopback-Geräte listet);
  Datei-Modus via soundfile (WAV/FLAC/MP3/OGG), Datei wird dabei **mit abgespielt** (thread-los im RAM).
- **Analyse:** numpy — FFT-Bänder (Bass/Mitten/Höhen), spektraler Fluss (Onset), Kick (Bass-Anstieg).
- **Beat-Tracker:** Tempo aus Inter-Onset-Intervallen (Median), Phasen-Snap auf **Kick-Onsets**,
  Free-Running dazwischen, `BeatState` mit **Beat-Envelope** `exp(-dt/tau)`.
- **Beat-Tap (Fallback):** Tap setzt Tempo+Phase, überschreibt Auto-Erkennung für 8 s.
- **Beat-Sync-Modell:** Effekt-Wechsel und Clip-Wechsel quantisiert auf Beat/Bar;
  Clip-Auto-Wechsel alle N Takte (default 4 Bars); Video **flüssig** (Prefetch-Decode-Thread, ≤720p),
  Frame-Step optional.
- **Effekte:** 7 (Reaktiver Hintergrund, Beat-Ring, Video, Bild Kick-Puls, Kugel-Wobble,
  Bass-Warp, RGB-Split), Tasten 1–9 / Space, alles skaliert über Beat-Envelope/Phase.
- **GUI (GL-UI, komplett in moderngl):** Thumbnail-Raster aller Clips aus `media/` (gepaged, klickbar),
  TAP-Button, BPM/Beat-Anzeige, Effektliste. Text via PIL→Textur (pyglet-2D neben moderngl malt nicht).
- **Clips:** Ordner `<exe-dir>/media/`, Scan beim Start, Thumbnails, kein direkter Repeat. Ziel: ~100 Clips.

## Tech-Stack
Python 3.11 · numpy · sounddevice · soundfile · pycaw+comtypes (win32) · opencv-python · Pillow ·
moderngl · pyglet · **PyInstaller onefile** → `SeAnimation-X.Y.Z.exe` (Version im Dateinamen).
CI: GitHub Actions (`ci.yml`: Unit-Tests auf ubuntu + Exe-Build auf windows; `release.yml` bei Tag `vX.Y.Z`
baut Exe und hängt sie als Release-Asset an). Fallback-Download: Branch `dist-exe` (`bin/SeAnimation-X.Y.Z.exe`).

## Repo / Artefakte
- Repo (privat): **github.com/thesepix/SeAnimation**, PR **#1**, Branch `vibe/anforderungen-1ac69e`.
- Doku: `ANFORDERUNGEN.md` (Anforderungen + Entscheidungsprotokoll), `README.md`, diese Datei.
- Releases: Tags `v0.2.0` … `v0.7.1` mit Exe-Assets. Desktop-getestet und bestätigt laufend: v0.5.0 (GUI+Effekte),
  v0.6.0 (Y-Flip, smooth Video, Sound-out), v0.7.x (Performance, GL-UI).
- Tests: 26 Unit-Tests grün in CI (Beat-Pipeline, WAV/FLAC, Library, ClipPlayer, Tap, Loopback-Pick).

## Betrieb auf dem Ziel-PC (kein Python nötig)
```powershell
# Exe aus Release laden nach C:\Desktop\SeAnimation, Clips nach C:\Desktop\SeAnimation\media
.\SeAnimation-0.7.1.exe --file .\Vletrmx.mp3   # GUI + Datei (spielt mit + analysiert)
.\SeAnimation-0.7.1.exe                       # GUI live: Player spielt, App hört per Loopback mit
.\SeAnimation-0.7.1.exe --check-audio         # Audio isoliert testen
.\SeAnimation-0.7.1.exe --selftest            # Beat-Pipeline-Regression
```
Tasten: 1–9 Effekt · Space nächster · T/TAP-Button Tap · F Fullscreen · ESC Ende. OBS: Fensteraufnahme auf „SeAnimation – Ausgabe".
Achtung PowerShell 5.1: kein `&&`, Befehle einzeln (sonst `>>`-Verkettung).

## Wichtige Einschränkungen der Entwicklungs-Umgebung
- Die KI-Sandbox ist Linux **ohne GPU/Audio/Windows-COM** — GL-, pyglet- und pycaw-Code kann dort nicht
  ausgeführt werden, nur `py_compile` + Unit-Tests. Hardware-Tests laufen auf dem Win11-Desktop des Nutzers;
  Fehler werden per Konsolen-Log/Screenshot gemeldet und per neuem Release gefixt.

## Offene Punkte / Nächste Schritte
1. Performance final verifizieren (v0.7.1: thread-loser Datei-Modus, Frame-Limiter ~60 fps, Prefetch-Decode).
2. Effekt-Design feinjustieren ( Nutzer-Feedback: „Effekte müssen mehr hermachen" ).
3. Step 2: Traktor-Laptop → Desktop (Netzwerk-Audio `NetworkSource` + MIDI/OSC-Clock).
4. OBS-Window-Capture verifizieren; ~100 Clips kuratieren; evtl. mehr Ebenen/Layering.
