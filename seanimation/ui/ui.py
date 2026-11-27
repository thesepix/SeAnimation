"""UI im Preview-Fenster (A5, A8, A10): BPM/Beat-Anzeige, Effektliste (Tasten 1-5,
klickbar), Tap-Button, Hotkey-Hinweise. Nur Maus + Tastatur.

Zeichnung läuft über pyglet (nach dem GL-Render des App-Handlers).
"""

from __future__ import annotations

import pyglet

TAP_RECT = (20, 20, 150, 60)          # x, y, w, h
EFFECT_ROW = (20, 40, 320, 28)        # x, w, h — y wird von oben gerechnet


class UI:
    def __init__(self, app, window):
        self.app = app
        self.window = window
        x, y, w, h = TAP_RECT
        self.tap_rect = pyglet.shapes.Rectangle(x, y, w, h, color=(190, 50, 50))
        self.tap_label = pyglet.text.Label(
            "TAP (T)", x=x + 30, y=y + 22, font_size=16,
            color=(255, 255, 255, 255), anchor_x="left", anchor_y="center",
        )
        self.bpm_label = pyglet.text.Label("", x=20, y=window.height - 30, font_size=20,
                                           color=(120, 255, 120, 255))
        self.beat_circle = pyglet.shapes.Circle(window.width - 60, window.height - 60, 12,
                                                color=(255, 200, 60))
        self.hint_label = pyglet.text.Label(
            "1-5 Effekt | Space nächster | T Tap | F Fullscreen | ESC Ende",
            x=20, y=window.height - 60, font_size=11, color=(160, 160, 160, 255),
        )
        self.effect_labels: list[pyglet.text.Label] = []
        for i in range(len(app.effects)):
            row_x, row_w, row_h = EFFECT_ROW[0], EFFECT_ROW[2], EFFECT_ROW[3]
            row_y = window.height - 100 - i * (row_h + 4)
            self.effect_labels.append(
                pyglet.text.Label("", x=row_x, y=row_y, font_size=13,
                                  color=(220, 220, 220, 255))
            )

    # ---------- Hit-Tests ----------
    def hit_tap(self, x, y) -> bool:
        x0, y0, w, h = TAP_RECT
        return x0 <= x <= x0 + w and y0 <= y <= y0 + h

    def hit_effect(self, x, y) -> int | None:
        _, _, row_w, row_h = EFFECT_ROW
        for i in range(len(self.app.effects)):
            row_y = self.window.height - 100 - i * (row_h + 4)
            if EFFECT_ROW[0] <= x <= EFFECT_ROW[0] + row_w and row_y <= y <= row_y + row_h:
                return i
        return None

    # ---------- Zeichnen ----------
    def draw(self) -> None:
        st = self.app.state
        bs = st.beat_state
        if bs is not None:
            env = bs.envelope(st.last_time)
            self.bpm_label.text = f"{bs.bpm:6.1f} BPM   Beat {bs.beat_number}" + ("  BAR" if bs.is_bar else "")
            self.beat_circle.radius = 10 + 26 * env
        else:
            self.bpm_label.text = "... warte auf Audio"
        active_id = (st.active_effect or {}).get("id")
        for i, label in enumerate(self.effect_labels):
            name = self.app.effects.get(i)["name"]
            mark = ">> " if self.app.effects.get(i)["id"] == active_id else f"{i + 1}. "
            label.text = mark + name
        # Tap-Button + Beat-Kreis + Labels zeichnen
        self.tap_rect.draw()
        self.tap_label.draw()
        self.beat_circle.draw()
        self.bpm_label.draw()
        self.hint_label.draw()
        for label in self.effect_labels:
            label.draw()
