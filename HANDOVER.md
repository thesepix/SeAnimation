# HANDOVER.md — Übergabe an die nächste KI / Entwickler:in

Zweck: Eine andere KI (oder ein Mensch) kann **jederzeit mittendrin übernehmen**,
auch wenn die vorherige Arbeit abgebrochen ist. Vor Beginn einer Aufgabe den
Abschnitt „Aktuelle Aufgabe" ausfüllen, nach jedem Teilschritt aktualisieren.

- Regeln für KI-Agenten: **[AGENTS.md](AGENTS.md)** (verbindlich)
- Mitwirkungs-Ablauf (PRs, Tests, Releases): **[CONTRIBUTING.md](CONTRIBUTING.md)**
- Anforderungen + Architektur + Entscheidungslog: **[ANFORDERUNGEN.md](ANFORDERUNGEN.md)**
- Versionshistorie: **[CHANGELOG.md](CHANGELOG.md)**
- Projekt-Überblick in 1 Minute: **[PROJEKT.md](PROJEKT.md)**

---

## Aktuelle Aufgabe

**Stand: 27.11.2026 — Repo-Standards/Handover-Aufrüstung (PR #3, Branch `vibe/handover-1ac69e`).**
PR #1 (gesamter Code) und PR #2 (Repo-Standards: AGENTS.md, CONTRIBUTING, Templates,
Dependabot, Ruleset auf `main`) sind gemerged. PR #3 ergänzt HANDOVER.md,
CHANGELOG.md, `tools/check.py`, `--shot`-PNG-Export, gepinnte requirements und ein
Test-Audio-Asset.

**Nächste fachliche Aufgaben (in dieser Reihenfolge):**
1. **Performance-Test durch den User mit v0.7.1/v0.8.0** — Datei-Modus
   (`SeAnimation-X.Y.Z.exe --file Vletrmx.mp3`, thread-los seit v0.7.1) und
   Live-Modus (Musik im externen Player, Loopback hört mit). Ergebnis: Konsolen-Log.
2. **Effekt-Design** — läuft gerade in PR #8 (Branch `vibe/effekte-1ac69e`):
   14 Effekte (neu: Sonnenstrahlen/Tunnel/Plasma/Kaleidoskop + Glitch/Pixel/Invert),
   Tasten 1-9,0. Danach: Look der neuen Effekte vom User auf Win11 bewerten
   (Shader-Parameter in `render/shaders/*.frag` nachjustieren).
3. **Step 2: Traktor-Verbindung** — Traktor läuft auf einem separaten Win11-Laptop,
   Visuals auf dem Desktop-PC. Optionen: Netzwerk-Audio (z. B. VBAN/RTP →
   `NetworkSource` als AudioSource) und/oder Traktor-MIDI/OSC-Clock als exakte
   Taktquelle (dockbar an die AudioSource/Clock-Abstraktion).
4. **OBS verifizieren** — Fensteraufnahme auf „SeAnimation – Ausgabe".
5. **~100 Clips** in `media/` kuratieren (Thumbnail-Raster paginiert bereits, 4×3/Seite).

## Letzter bekannter guter Stand

- **Tag `v0.7.1`** ↔ `SeAnimation-0.7.1.exe` (Release-Asset, PE-verifiziert, 80.333.072 Bytes)
- `main` nach Merge PR #2: Commit `29d87cf` (Code + Repo-Standards)
- Branch `vibe/anforderungen-1ac69e` existiert weiter (Delivery-Branch, nicht löschen)
- Exe-Fallback: Branch `dist-exe` → `bin/SeAnimation-0.7.1.exe` + `bin/SeAnimation.exe`
- Tests: 26 Unit-Tests + Selftest PASS (90–190 BPM, Phasenfehler 33–41 ms)
- User-seitig bestätigt (v0.5.0): GUI öffnet, Loopback-Audio läuft, erster Beat
  erkannt, Effekte schalten quantisiert auf Beat, Clips laden aus `media/`

## Versucht und gescheitert (nicht wiederholen)
| Versuch | Problem | Lösung (aktuell) |
|---|---|---|
| PortAudio-Loopback als Audioquelle | listet auf Win11 oft keine Loopback-Geräte | pycaw/Core-Audio `WasapiLoopbackSource` (`AUDCLNT_STREAMFLAGS_LOOPBACK`) |
| ein geteilter pyglet-GL-Context für 2 Fenster | `RuntimeError: Canvas has not been attached` | **eigener GL-Kontext pro Fenster** (`_WindowGL`) |
| pyglet-2D-UI gemischt mit moderngl | UI unsichtbar/weiße Fenster | UI komplett in moderngl (PIL-Text → Texturen, Quads) |
| Uniforms blind setzen | `KeyError: u_beat_phase` (Treiber strippt ungenutzte Uniforms) | defensives `_set()` |
| `window.on_draw = ...` | überschreibt pyglet-Handler | `push_handlers(...)` |
| Bilder/Videos direkt in GL-Textur | kopfstehend | Y-Flip (`frame[::-1]`) einmalig beim Upload/Prefetch |
| `--file` mit Fanout-Queue + Source-Thread | Stottern bei halber Geschwindigkeit | thread-los: Datei komplett im RAM, Wiedergabe per `sounddevice.OutputStream`-Callback, Analyse per Wallclock im Render-Loop |
| Video-Decode im Render-Thread | Ruckeln | Prefetch-Thread mit bounded Queue (neuestes Frame gewinnt), Downscale ≤720p |
| `prefetch=True` als Default in ClipPlayer | avcodec-Crash `fctx->async_lock failed` in sync-Tests | Default `prefetch=False`, App setzt `prefetch=True` |
| WAV nur 8/16/32-bit | 24-bit WAV crashte | soundfile/libsndfile für `--file` (WAV/FLAC/MP3/OGG), WavFileSource als Fallback mit 24-bit |
| `gh pr merge` / REST-API-Mutationen aus der Agent-Sandbox | `Merging via CLI is not allowed` / `Mutating GitHub API calls are not allowed` | Merge + Repo-Settings (Description/Topics/Ruleset) macht der User im Web-UI; Agent pusht Branches/Tags |
| pycaw `Activate(cls, ...)` / `Interface` statt `_iid_` | `TypeError: expected LP_GUID` | `Activate(IAudioClient._iid_, ...)` + `cast(..., POINTER(...))`, `GetMixFormat()` via `.contents`, `CoInitialize()` |

## Offene Punkte

- GitHub Issues (aktuell): Dependabot-Action-Bumps **#3–#6** — reviewen & mergen
  https://github.com/thesepix/SeAnimation/issues
- Feature-Backlog: siehe „Aktuelle Aufgabe" Punkte 2–5 oben
- Neue Bugs/Ideen → Issue-Templates unter `.github/ISSUE_TEMPLATE/`

## Umgebungsnotizen (nur für die Agent-Sandbox — NICHT projektspezifisch)

- Der Agent arbeitet **nur** im isolierten Linux-Sandbox-Clone
  `/workspace/github__thesepix__SeAnimation`; der Mac des Users wird nie angefasst.
- Sandbox: kein GPU, kein Audio, kein COM → GL/pycaw-Code hier nur `py_compile`;
  Hardware-Test macht der User auf dem Win11-Desktop mit der Release-Exe.
- `gh`-CLI ist authentifiziert, aber **Mutationen an PRs/Repo-Settings sind blockiert**
  (Merge, `repo edit`, Rulesets) — der User klickt im Web-UI.
- `curl` ist in der Sandbox verboten (Web-Zugriff nur über die Web-Tools).
- PowerShell 5.1 auf dem User-PC: **kein `&&`**, Befehle einzeln oder mit `;` trennen.
- CI: `ci.yml` läuft auf `pull_request` + `workflow_dispatch` (kein push-Trigger,
  sonst Bot-Push-Loop auf `dist-exe`); Tests auf ubuntu (numpy/soundfile/cv2/pillow),
  Exe-Build auf windows-latest.
