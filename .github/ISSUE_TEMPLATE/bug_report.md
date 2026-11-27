---
name: Bug report
description: Etwas funktioniert nicht wie erwartet
title: "bug: "
labels: ["bug"]
body:
  - type: textarea
    id: what-happened
    attributes:
      label: Was ist passiert?
      description: Beschreibe das unerwartete Verhalten.
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Was hättest du erwartet?
    validations:
      required: true
  - type: textarea
    id: repro
    attributes:
      label: Schritte zur Reproduktion
      description: "z. B.: 1. Exe starten 2. `--file track.mp3` 3. Taste 3 drücken"
      value: |
        1.
        2.
        3.
    validations:
      required: true
  - type: textarea
    id: log
    attributes:
      label: Konsolen-Log / Traceback
      description: Komplette PowerShell-Ausgabe beim Auftreten des Fehlers (inkl. `[PYI-...]`-Zeilen der Exe). Bitte als Code-Block einfügen.
    validations:
      required: true
  - type: input
    id: exe-version
    attributes:
      label: Exe-Version
      description: "z. B. SeAnimation-0.7.1.exe (steht im Dateinamen) oder `--version`"
    validations:
      required: true
  - type: input
    id: windows
    attributes:
      label: Windows-Version
      description: "z. B. Windows 11 23H2, Build 22631"
    validations:
      required: true
  - type: input
    id: audio-mode
    attributes:
      label: Audio-Modus
      description: "Live (WASAPI-Loopback, keine Argumente) oder `--file <track>`? Welches Audio-Interface (z. B. Focusrite Scarlett)?"
  - type: textarea
    id: screenshot
    attributes:
      label: Screenshot
      description: Bild einfügen (Drag & Drop) oder Link — besonders bei GL-/Darstellungsfehlern.
  - type: checkboxes
    id: checks
    attributes:
      label: Vorab geprüft
      options:
        - label: "`\\SeAnimation-<X.Y.Z>.exe --selftest` läuft durch mit `ERGEBNIS: PASS`"
        - label: "`\\SeAnimation-<X.Y.Z>.exe --check-audio` meldet `ERGEBNIS: PASS`"
---
