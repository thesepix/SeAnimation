# Mitwirken an SeAnimation (Contributing)

Danke fürs Mitmachen! Dieses Repo wird gemeinsam von Mensch und mehreren
KI-Agenten gepflegt — bitte halte dich an die Abläufe unten, dann bleiben
Diffs klein, Review einfach und Releases nachvollziehbar.

> **Für KI-Agenten (Claude, Copilot, …):** Lies zuerst **[AGENTS.md](AGENTS.md)**
> — dort stehen die verbindlichen Regeln (Branch-Schema, Versionierung,
> Test-Pflicht, Sprachkonventionen).

## 1. Arbeiten am Code

1. Issue anlegen (oder vorhandenes zuweisen) — Bug oder Feature.
2. Branch von `main` abzweigen, Schema: `vibe/<kurz-slug>-1ac69e`
   ```powershell
   git checkout main
   git pull
   git checkout -b vibe/mein-thema-1ac69e
   ```
3. Entwickeln. **Nie direkt auf `main` pushen.** Branch nach dem Merge nicht löschen.
4. Lokal testen (Pflicht, siehe unten).
5. Draft-PR öffnen (Template wird automatisch geladen, siehe
   `.github/PULL_REQUEST_TEMPLATE.md`). Der Maintainer markiert "ready for
   review" und merged (Squash bevorzugt).

## 2. Pflicht-Tests vor jedem PR

```powershell
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m seanimation --selftest
```

Beides muss grün sein (`ERGEBNIS: PASS`). GL-/Audio-Hardware-Verhalten kann in
der CI-Sandbox nicht laufen — das testet der Maintainer auf dem Win11-Desktop
mit der Release-Exe (Log + Screenshot im PR beschreiben).

## 3. Versionierung & Releases

- SemVer in `seanimation/__init__.py` (`__version__`) **und** `pyproject.toml` gemeinsam bumpen.
- Release = **annotated Tag** `vX.Y.Z`:
  ```powershell
  git tag -a v0.8.0 -m "v0.8.0: <kurzbeschreibung>"
  git push origin v0.8.0
  ```
- Der Workflow `release.yml` baut automatisch die Windows-Exe
  (`SeAnimation-0.8.0.exe`) und hängt sie an ein GitHub Release an
  (Fallback bei Quota: Branch `dist-exe` → `bin/`).
- Tag ↔ Datei: `v0.8.0` ↔ `SeAnimation-0.8.0.exe`. Nie eine Version erfinden.
- Entscheidungen/Änderungen am Verhalten ins Entscheidungsprotokoll in
  `ANFORDERUNGEN.md` §10 eintragen.

## 4. Code-Konventionen

- Python 3.11, 4 Spaces (siehe `.editorconfig`), Module lazy-importieren, damit
  die Tests headless ohne GL/Audio laufen.
- User-facing Texte (UI, Konsolen-Meldungen, Doku) **deutsch**; Code, Kommentare,
  Commits, PR-Titel **englisch**.
- PowerShell-Befehle für den User: **kein `&&`** (PowerShell 5.1!), ein Befehl
  pro Zeile oder `;` als Trenner.
- Beat-Sync-Modell und Architektur siehe `ANFORDERUNGEN.md` §3/§5 — vor
  Verhaltensänderungen lesen.
- `media/` (lokale Clips des Users) wird nicht versioniert.

## 5. PR-Checkliste

- [ ] Tests grün (`unittest` + `--selftest`)
- [ ] Version gebumpt (falls Release) in `__init__.py` + `pyproject.toml`
- [ ] Doku aktualisiert (`README.md` / `ANFORDERUNGEN.md`), falls CLI oder Verhalten sich ändert
- [ ] PR-Template vollständig ausgefüllt, Issue verlinkt (`Closes #N`)
- [ ] CI grün (Job `test` auf ubuntu; `build-exe` baut die Exe auf windows-latest)

## 6. Issues

- Bugs → Template **Bug report** (Log/Screenshot, Exe-Version, Windows-Version)
- Ideen → Template **Feature request**
- Sicherheitsprobleme → siehe `.github/SECURITY.md`

## 7. Lizenz

Beiträge stehen unter **GPL-3.0** (siehe [LICENSE](LICENSE)).
