---
name: Feature request
description: Idee für eine neue Funktion oder Verbesserung
title: "feature: "
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Welches Problem soll gelöst werden?
      description: Ausgangspunkt — z. B. "die Effekte wirken billig", "kein Beat bei Track X".
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Vorgeschlagene Lösung
      description: Wie stellst du dir das vor? (Effekt-Idee, UI, CLI-Option, Traktor-Anbindung …)
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternativen, an die du gedacht hast
  - type: textarea
    id: context
    attributes:
      label: Zusatzkontext
      description: Screenshots, Beispiel-Tracks, Links, betroffene Stelle im Code.
---
