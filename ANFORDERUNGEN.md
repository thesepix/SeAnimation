# Anforderungsdokument — SeAnimation

Beat-synchrone Musik-Visuals für Windows 11. Dieses Dokument ist die
verbindliche Grundlage für die Implementierung. Änderungen daran werden
über Pull Requests vorgenommen.

Status: **v1.0 — Anforderungen mit dem Auftraggeber abgestimmt**

---

## 1. Projektziel

Eine Software auf einem **Windows-11-Desktop-PC**, die während der
Musikwiedergabe beat-synchrone Visuals erzeugt: kurze Video-/Bild-Clips
und generierte Effekte, bei denen **jede sichtbare Änderung im Takt der
Musik** passiert. Ausgabe wahlweise im Preview-Fenster der Software oder
in einem eigenen randlosen Fenster (Vollbild / OBS-Einbindung).

## 2. Systemkontext & Randbedingungen

| Aspekt | Festlegung |
|---|---|
| Visuals-Rechner | Windows-11-Desktop-PC (dort läuft auch **OBS** beim Streamen) |
| DJ-Quelle (Step 2) | Traktor auf einem **separaten Windows-11-Laptop** — später angebunden |
| Test im MVP | beliebige Musik wird **lokal auf dem Desktop-PC** abgespielt |
| Audioquelle (MVP) | Standard-/erstes verfügbares Windows-Audiogerät, aufgenommen als **WASAPI-Loopback** ("Was du hörst"); später in der UI wählbar |
| Quellen | Bilder und Videos aus einem lokalen Ordner |
| Steuerung | **nur Tastatur und Maus** (keine MIDI-Controller-Steuerung im MVP) |
| Sprache/Stack | **Python** (schnelle Iteration, starke C-Bibliotheken für Audio/Video/GL) |

## 3. Funktionale Anforderungen

### 3.1 Audioeingang (A1–A2)
- **A1** Aufnahme des System-Audio über WASAPI-Loopback in einen Ringpuffer.
- **A2** Die Audioquelle ist als austauschbares Modul (`AudioSource`) gekapselt.
  Step 2: `NetworkSource` (Audio-Stream vom Traktor-Laptop, z. B. VBAN/RTP)
  dockt ohne Änderung am Rest an.

### 3.2 Audio-Analyse (A3–A4)
- **A3** Spektrum per FFT in Bändern (Bass / Mitten / Höhen) + Onset-Erkennung.
- **A4** Beat- und Tempo-Erkennung aus dem Signal: BPM + Beat-Phase pro Frame
  (Implementierung: numpy — Onset via spektralem Fluss, Tempo aus
  Inter-Onset-Intervallen, Phase per Snap auf Onsets; aubio/librosa optional in Step 2).

### 3.3 Beat-Sync-Modell (Kernspezifikation, abgestimmt)
Das zentrale Versprechen: **das Visuelle passiert im Takt.** Konkret:

1. **Beat-Envelope:** Jeder Effekt-Parameter erhält auf jedem Beat einen
   Impuls, der bis zum nächsten Beat exponentiell abklingt:
   `env(dt) = exp(-dt / tau)` mit `dt` = Zeit seit letztem Beat.
   Beispiel Kugel-Wobble: Bild wird per Shader zur Kugel geformt; die
   Wobble-Amplitude = Impuls auf dem Beat + kleiner Grundwert → die Kugel
   wackelt bei jedem Schlag und beruhigt sich dazwischen.
2. **Frame-Step-Video:** Videos laufen nicht frei in Echtzeit, sondern werden
   **pro Beat um genau ein Frame weitergeschaltet** (Stop-Motion-Prinzip).
   Dadurch ist jede sichtbare Änderung im Video garantiert auf dem Beat.
   Loop-Länge = N Beats (Default: 4), danach Replay oder nächster Clip.
3. **Quantisierte Starts/Wechsel:** Animationen starten oder wechseln nie
   mitten im Takt, sondern auf Beat- oder Taktlinien (Scheduler mit Lookahead).
4. **Bilder:** Beat-Puls-Effekte (kurz größer / heller / rotiert auf jedem
   Beat), Farbe kann pro Takt wechseln; optional Ken-Burns mit Beat-Phase.

### 3.4 Animations-Bibliothek (A5–A6)
- **A5** Ordner mit Bildern und Videos; in der UI ein **Thumbnail-Raster**
  (Buttons), Klick aktiviert die Animation. Zielausbau: **~100 Einträge**;
  **MVP: 5 fest eingebaute Test-Animationen** (siehe Abschnitt 7).
- **A6** Auswahl ohne direkten Repeat: kürzlich gespielte Animationen werden
  vorübergehend aus der Zufallsauswahl ausgeschlossen.
- **MVP-Umfang:** **eine aktive Animation / ein Effekt zur Zeit**.

### 3.5 Ausgabe (A8–A9)
- **A8** **Preview-Fenster:** zeigt die Animation plus Bedien-UI
  (Thumbnail-Raster, Effekt-Buttons, BPM-/Beat-Anzeige).
- **A9** **Ausgabefenster:** nur die Animation, randlos, per Hotkey/Button auf
  Vollbild schaltbar; in OBS als **Fensteraufnahme (Window Capture)** einbindbar.

### 3.6 Steuerung (A10)
- Nur Maus/Tastatur. Geplante Hotkeys: **Leertaste** = nächste Animation,
  **Pfeiltasten** = Auswahl im Thumbnail-Raster, **F** = Vollbild umschalten,
  Mausklick auf Thumbnail = Animation aktivieren.

### 3.7 Stabilität (A11)
- Clips werden vorgepuffert (Preloading), damit Wechseln ruckelfrei ist.
- Automatischer Fallback auf den generativen Hintergrund, wenn ein Clip
  fehlt oder nicht dekodiert — die Software darf nie stehen bleiben.

## 4. Nicht-funktionale Anforderungen

- **N1** 60 fps auf dem Ausgabefenster; Audio→Bild-Latenz < ~100 ms.
- **N2** Windows 11, möglichst ohne Admin-Rechte.
- **N3** MVP-Konfiguration hartkodiert (`config.py`); später Config-Datei.
- **N4** Lizenz: GPL-3.0 (siehe `LICENSE`).

## 5. Architektur (Module & Datenfluss)

```
AudioSource (WASAPI-Loopback) ─┐
                               ├─► Ringpuffer ─► Analyzer (FFT, Bänder, Onset)
Netzwerk-Quelle (Step 2) ──────┘                        │
                                                        ▼
                                               BeatTracker (BPM + Phase)
                                                        │
                                                        ▼
                                        Scheduler (Beat-Grid, Lookahead-Events:
                                         quantisierte Clip-Wechsel/Effekt-Trigger)
                                                        │
Library (Ordner-Scan, Thumbnails, ─► aktive Animation ─┴─► Renderer (moderngl, Layer-Compositing)
 Auswahl ohne Repeat)                                                  │
                                                          ┌─────────────┴─────────────┐
                                                          ▼                           ▼
                                                Preview-Fenster (mit UI)     Ausgabe-Fenster (randlos/
                                                                               Vollbild, OBS Window Capture)
```

Module (Paket `seanimation/`):
`audio/` (AudioSource, LoopbackSource) · `analysis/` (Analyzer, BeatTracker) ·
`clock/` (Scheduler) · `library/` (Library, Thumbnails) · `render/` (Renderer,
Effects, GLSL-Shader) · `ui/` (UI) · `config.py`, `main.py`.

## 6. Technologie-Stack

Python 3.11+ mit: **sounddevice** (WASAPI-Loopback), **numpy** (FFT, Band-Energien,
eigener Beat-/Tempo-Tracker), **opencv-python** + **Pillow** (Video-Dekodierung,
Thumbnails), **moderngl** + **moderngl-window** (OpenGL-Rendering, zwei Fenster,
Maus/Tastatur).

Begründung Python: Die schwere Arbeit (FFT, Dekodierung, GL) passiert in
C-Bibliotheken; Python beschleunigt die Iteration. C#/.NET wäre nur bei
späterem Bedarf an maximaler Performance nötig — dank Modul-Abstraktion
portierbar.

## 7. MVP-Lieferumfang — 5 eingebaute Test-Animationen

1. **video_frame_step** — Video im Frame-Step (1 Frame pro Beat, Loop über 4 Takte)
2. **image_kick_pulse** — Bild wird auf jedem Beat kurz größer + heller
3. **sphere_wobble** — Video/Bild wird per Shader zur Kugel geformt, wackelt pro Beat
4. **reactive_bg** — generativer Hintergrund: Bass treibt Wellen/Partikel, Kick = Blitz
5. **beat_ring** — Vollbild-Ring/Blitz auf jedem Beat, Farbe wechselt pro Takt

## 8. Step 2 / später (nicht MVP)

- **Traktor-Verbindung:** Audio-Stream vom Laptop (VBAN/RTP) als `NetworkSource`
  und/oder Traktor-Clock (MIDI/OSC) als externe Clock — dank A2 ohne Umbau.
- Layering mehrerer Animationen gleichzeitig (Ebenen-Stapel statt einer aktiven).
- Tempo-Match: Clips per Abspielrate exakt in N Takte dehnen.
- Weitere Ausgabe: Spout-Sender oder virtuelle Kamera fürs Streaming.
- UI-Wählbarkeit des Audiogeräts; Config-Datei statt hartkodierter Werte.

## 9. Test & Betrieb

- Die Entwicklungs-Sandbox kann die Software **nicht ausführen** (kein Windows/
  Audio/GPU). Testlauf erfolgt auf dem Win11-Desktop-PC:
  `git clone` → `pip install -r requirements.txt` → `python -m seanimation`.
- Headless-Test der Beat-Pipeline (läuft auch ohne Audiohardware/GPU, z. B. in der
  Sandbox): `python -m seanimation --selftest` bzw. `python -m unittest discover -s tests`.
  WAV-Datei als Audioquelle: `python -m seanimation --wav track.wav`.
- Entwicklungs-Workflow: Branch `vibe/<slug>-1ac69e` in diesem Repo, Änderungen
  als Draft-PR mit sichtbarem Diff; Review auf GitHub, dann Merge.
- Fehlerbehebung im Kreislauf: Symptom + Konsolenausgabe melden → Fix im PR → Pull.

## 10. Getroffene Entscheidungen (Protokoll)

| Datum | Entscheidung |
|---|---|
| v1.0 | Beat-Erkennung reicht im MVP; Traktor-Anbindung ist Step 2 |
| v1.0 | Visuals auf Desktop-PC, Traktor auf separatem Laptop; OBS lokal |
| v1.0 | Ausgabe: Preview-Fenster + eigenes randloses Ausgabefenster (OBS Window Capture) |
| v1.0 | Quellen: Bilder + Videos; Videos im Frame-Step (jede Änderung im Takt) |
| v1.0 | Beat-Sync über Beat-Envelope (Impuls + exponentielles Abklingen) und quantisierte Starts |
| v1.0 | MVP: 5 eingebaute Test-Animationen, eine aktive zur Zeit, ~100 Ordner-Einträge als Ziel |
| v1.0 | Steuerung nur per Tastatur/Maus |
| v1.0 | Audioquelle MVP: Standard-/erstes Windows-Audiogerät (WASAPI-Loopback) |
| v1.0 | Stack: Python (moderngl-window, sounddevice, numpy/scipy, aubio, opencv, Pillow) |
| v1.0 | Lieferung ausschließlich über GitHub-PR in `thesepix/SeAnimation` |
| v1.1 | Beat-Tracker als eigene numpy-Implementierung (Onset-Fluss + IOI-Median + Phasen-Snap); aubio/librosa aus requirements entfernt (Installationsrisiko auf Windows), optional in Step 2 |
| v1.1 | Testquellen ohne Hardware: `SynthSource` (Kick+Click bei BPM) und `WavFileSource`; Selftest via `python -m seanimation --selftest` |
