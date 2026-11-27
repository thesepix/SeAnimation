# AGENTS.md — Instructions for AI coding agents

This file is read automatically by AI assistants (Claude, Copilot, Codex, Gemini, …).
Follow it when working on this repository. Product documentation is in German
(`ANFORDERUNGEN.md`, `PROJEKT.md`, `README.md`); write code comments, commit
messages and PR descriptions in English unless the user asks otherwise.

## What this project is

**SeAnimation** — beat-synced music visuals for **Windows 11**, written in
**Python 3.11**, delivered as a **standalone `.exe`** (PyInstaller onefile).
It captures all Windows audio (WASAPI loopback "what you hear") or plays a file
(`--file`), detects the beat (FFT bands / onsets / kick), and renders generative
GLSL shader effects plus short video/image clips from a `media/` folder — every
visible change is quantized to the beat/bar. Two windows: a Preview window with
a clickable GL-UI (thumbnail grid, TAP button, effect list) and a borderless
Output window that OBS captures via Window Capture. Primary use case: live DJ
sets with Traktor (Traktor runs on a separate laptop; visuals run on the desktop
PC next to OBS).

**This is a native Windows desktop app (pyglet + moderngl/OpenGL), NOT a
browser WebGL/Web Audio app.** Do not suggest web technologies for the core.

## Repository layout

```
seanimation/            Python package
  audio/                AudioSource abstraction: WASAPI loopback (pycaw, win32),
                        PortAudio loopback (sounddevice), file sources (soundfile /
                        stdlib wav), synth test source
  analysis/             analyzer.py (FFT bands, spectral flux, kick) + beat.py
                        (BeatTracker: onset IOI tempo, kick phase-snap, tap override)
  library/              media/ scanning, thumbnails, ClipPlayer (OpenCV, prefetch
                        thread, downscale <=720p, Y-flip, bounded queue)
  render/               renderer.py (one moderngl context per window), effects.py,
                        shaders/ (*.vert/*.frag, fullscreen triangle)
  ui/                   GL-UI (PIL text -> textures, quads, hit tests)
  app.py, main.py, devtest.py, config.py, __main__.py
tests/                  unittest suite (headless: numpy/soundfile/cv2 only)
.github/workflows/      ci.yml (tests on ubuntu + exe build on windows-latest),
                        release.yml (tag vX.Y.Z -> GitHub Release with exe asset;
                        fallback: push exe to branch dist-exe/bin/)
scripts/build_exe.ps1   local PyInstaller build
seanimation.spec        PyInstaller onefile spec; exe name = SeAnimation-<__version__>.exe
media/                  user's clips (NOT versioned, see .gitignore) — next to the
                        exe when frozen
```

## Commands

```bash
pip install -r requirements.txt        # dev setup (Python 3.11+, pinned versions)
python tools/check.py                  # ONE command before every commit: syntax + tests + selftest
python -m unittest discover -s tests -v # test suite (headless-safe)
python -m seanimation --selftest        # beat pipeline self-test (no audio hardware)
python -m seanimation --analyze --file track.flac   # CLI file analysis
python -m seanimation --file track.mp3  # GUI + file audio (plays through speakers)
python -m seanimation                   # GUI + WASAPI loopback (live, win32 only)
python -m seanimation --shot out.png --file tests/assets/beat_124bpm.wav --effect 0
                                        # headless render -> PNG (needs GPU, Windows desktop;
                                        # without --file a synth signal at --bpm is used)
pyinstaller seanimation.spec --clean --noconfirm   # local exe build -> dist/
```

## Doc map (read before changing behaviour)

- `AGENTS.md` — this file (rules for AI agents)
- `HANDOVER.md` — current task, last known good state, tried-and-failed list,
  open issues, environment notes (update after every work step!)
- `CHANGELOG.md` — version history (Keep a Changelog); add entries under Unreleased
- `ANFORDERUNGEN.md` — full requirements + architecture + decision log (German)
- `PROJEKT.md` — 1-minute summary for external AIs
- `CONTRIBUTING.md` — PR workflow, mandatory checks, release process
- `README.md` — user-facing quickstart

## Hard rules

1. **`main` is protected-by-convention: never push directly to `main`.** Work on
   a task branch `vibe/<short-slug>-1ac69e` and open a **draft PR**; the human
   reviews and merges on GitHub. Do not delete task branches after merge.
2. **Versioning:** bump `__version__` in `seanimation/__init__.py` AND
   `pyproject.toml` together (SemVer). Releases = annotated tag `vX.Y.Z`
   ↔ file `SeAnimation-X.Y.Z.exe`. Never invent a version.
3. **Do not touch branch `dist-exe`** manually — it is written only by the
   `ci`/`release` workflows (exe fallback storage).
4. **`media/` is gitignored** — never commit user clips.
5. **Win32-only code** (`pycaw`, `comtypes`, WASAPI, pyglet GL windows) cannot run
   in a Linux CI sandbox — only `py_compile` it there. Hardware/GL behaviour is
   tested by the human on the Win11 desktop with the release exe. Keep heavy deps
   lazy-imported so the headless test suite runs with numpy/soundfile/cv2 only.
6. **German for user-facing text** (UI strings, console messages aimed at the
   user, README/CONTRIBUTING); **English for code, comments, commits, AGENTS.md**.
7. When giving the user PowerShell commands: **PowerShell 5.1 has no `&&`** — one
   command per line, use `;` as separator.
8. Tests must stay green: `python -m unittest discover -s tests` and
   `python -m seanimation --selftest` (PASS expected).

## Conventions

- Beat-sync model and all product decisions are documented in
  `ANFORDERUNGEN.md` (German, incl. decision log §10) — read it before changing
  behaviour. `PROJEKT.md` is a short summary for external AIs.
- Render loop is frame-limited (~60 fps per window); video decode runs in a
  prefetch thread with a bounded "newest frame wins" queue; textures are
  uploaded without `tobytes()`; skip upload when `frame_seq` unchanged.
- Every visual change (effect switch, clip switch) is applied **on the beat**
  via the beat-envelope model in `analysis/beat.py`.
- UI is drawn entirely in moderngl (pyglet 2D does not mix with moderngl);
  each window has its **own** GL context; events via `push_handlers`.
- Shaders must only use uniforms that are actually set: the renderer uses a
  defensive `_set()` helper because drivers strip unused uniforms.

## Definition of done for a change

- `python tools/check.py` PASS (syntax + unittest + selftest).
- Docs updated if behaviour/CLI changed (`README.md`, `ANFORDERUNGEN.md` log).
- PR description filled from `.github/PULL_REQUEST_TEMPLATE.md`, linked to an
  issue if one exists (`Closes #N`).
- `HANDOVER.md` "Aktuelle Aufgabe" updated; `CHANGELOG.md` entry added.

## Environment notes (agent sandbox only — not project facts)

- The agent works only in an isolated Linux clone at
  `/workspace/github__thesepix__SeAnimation`; the user's Mac is never touched.
- No GPU/audio/COM in the sandbox: GL and pycaw code is only `py_compile`-checked
  here; the human tests on the Win11 desktop with the release exe.
- `gh` is authenticated, but PR/repo-setting mutations are blocked for the agent
  ("Merging pull requests via CLI is not allowed") — the human merges in the web UI.
- `curl` is forbidden in the sandbox (use the web tools).
