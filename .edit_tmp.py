import io

# ---- effects.py: 7 -> 14 Effekte (bestehende Indizes 0-6 bleiben stabil) ----
p = "seanimation/render/effects.py"
s = io.open(p, encoding="utf-8").read()
old = '''EFFECTS_MVP = [
    {"id": "reactive_bg",  "name": "Reaktiver Hintergrund", "kind": "bg"},
    {"id": "beat_ring",    "name": "Beat-Ring",             "kind": "ring"},
    {"id": "clip_video",   "name": "Video smooth",          "kind": "clip_video",   "clip_kind": "video"},
    {"id": "clip_image",   "name": "Bild Kick-Puls",        "kind": "clip_image",   "clip_kind": "image"},
    {"id": "clip_wobble",  "name": "Kugel-Wobble",          "kind": "clip_wobble",  "clip_kind": "video"},
    {"id": "clip_distort", "name": "Bass-Warp",             "kind": "clip_distort", "clip_kind": "video"},
    {"id": "clip_split",   "name": "RGB-Split",             "kind": "clip_split",   "clip_kind": "video"},
]'''
new = '''EFFECTS_MVP = [
    # generative Hintergründe (bg.frag, u_mode) — Indizes 0-6 bleiben stabil (Tests/Keys)
    {"id": "reactive_bg",  "name": "Bass-Wellen",           "kind": "bg", "mode": 0},
    {"id": "beat_ring",    "name": "Beat-Ring",             "kind": "ring"},
    {"id": "clip_video",   "name": "Video smooth",          "kind": "clip_video",   "clip_kind": "video"},
    {"id": "clip_image",   "name": "Bild Kick-Puls",        "kind": "clip_image",   "clip_kind": "image"},
    {"id": "clip_wobble",  "name": "Video Kugel-Wobble",    "kind": "clip_wobble",  "clip_kind": "video"},
    {"id": "clip_distort", "name": "Video Bass-Warp",       "kind": "clip_distort", "clip_kind": "video"},
    {"id": "clip_split",   "name": "Video RGB-Split",       "kind": "clip_split",   "clip_kind": "video"},
    # neue generative Hintergründe (v0.8.0)
    {"id": "sunburst",     "name": "Sonnenstrahlen",        "kind": "bg", "mode": 1},
    {"id": "tunnel",       "name": "Tunnel-Zoom",           "kind": "bg", "mode": 2},
    {"id": "plasma",       "name": "Plasma",                "kind": "bg", "mode": 3},
    {"id": "kaleido",      "name": "Kaleidoskop",           "kind": "bg", "mode": 4},
    # neue Clip-Effekte (v0.8.0, clip.frag)
    {"id": "clip_glitch",  "name": "Video Glitch-Slices",   "kind": "clip_glitch",  "clip_kind": "video"},
    {"id": "clip_pixel",   "name": "Bild Pixel-Puls",       "kind": "clip_pixel",   "clip_kind": "image"},
    {"id": "clip_invert",  "name": "Bild Invert-Flash",     "kind": "clip_invert",  "clip_kind": "image"},
]'''
assert old in s, "effects list"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("effects.py OK")

# ---- renderer.py: u_mode + neue Clip-Uniforms ----
p = "seanimation/render/renderer.py"
s = io.open(p, encoding="utf-8").read()
old = '''            _set(prog, "u_kick", kick)
            _set(prog, "u_wobble", 1.0 if kind == "clip_wobble" else 0.0)
            _set(prog, "u_pulse", 1.0 if kind == "clip_image" else 0.0)
            _set(prog, "u_distort", 1.0 if kind == "clip_distort" else 0.0)
            _set(prog, "u_split", 1.0 if kind == "clip_split" else 0.0)'''
new = '''            _set(prog, "u_kick", kick)
            _set(prog, "u_wobble", 1.0 if kind == "clip_wobble" else 0.0)
            _set(prog, "u_pulse", 1.0 if kind == "clip_image" else 0.0)
            _set(prog, "u_distort", 1.0 if kind == "clip_distort" else 0.0)
            _set(prog, "u_split", 1.0 if kind == "clip_split" else 0.0)
            _set(prog, "u_glitch", 1.0 if kind == "clip_glitch" else 0.0)
            _set(prog, "u_pixel", 1.0 if kind == "clip_pixel" else 0.0)
            _set(prog, "u_invert", 1.0 if kind == "clip_invert" else 0.0)'''
assert old in s, "renderer clip uniforms"
s = s.replace(old, new, 1)
old = '''            prog = g.prog_bg
            _set(prog, "u_res", (win.width, win.height))'''
new = '''            prog = g.prog_bg
            _set(prog, "u_mode", float(eff.get("mode", 0)))
            _set(prog, "u_res", (win.width, win.height))'''
assert old in s, "renderer bg u_mode"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("renderer.py OK")

# ---- app.py: Tasten 1-9,0 ----
p = "seanimation/app.py"
s = io.open(p, encoding="utf-8").read()
old = '''        for i in range(9):  # Tasten 1-9
            k = getattr(key, f"_{i + 1}", None)
            if k is not None and symbol == k and i < len(self.effects):
                self.state.pending_effect_idx = i
                return True'''
new = '''        keynames = [f"_{n}" for n in range(1, 10)] + ["_0"]  # Tasten 1-9, 0 = erste 10 Effekte
        for i, kn in enumerate(keynames):
            k = getattr(key, kn, None)
            if k is not None and symbol == k and i < len(self.effects):
                self.state.pending_effect_idx = i
                return True'''
assert old in s, "app keys"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("app.py OK")

# ---- ui.py: Hint ----
p = "seanimation/ui/ui.py"
s = io.open(p, encoding="utf-8").read()
old = 'hint = "1-9 Effekt | Space n\\u00e4chster | T Tap | F Fullscreen | ESC Ende | Klick: Clip"'
if old not in s:
    old = 'hint = "1-9 Effekt | Space nächster | T Tap | F Fullscreen | ESC Ende | Klick: Clip"'
assert old in s, "ui hint"
new = 'hint = "1-9,0 Effekt (erste 10) | Space nächster | T Tap | F Fullscreen | ESC Ende | Klick: Clip"'
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ui.py OK")

# ---- main.py: Startup-Hinweis + --effect Help ----
p = "seanimation/main.py"
s = io.open(p, encoding="utf-8").read()
old = 'print("Tasten: 1-5 Effekt | Space nächster | T Tap | F Fullscreen | ESC Ende")'
assert old in s, "main hint"
s = s.replace(old, 'print("Tasten: 1-9,0 Effekt | Space nächster | T Tap | F Fullscreen | ESC Ende")', 1)
old = 'help="Effekt-Index für --shot (0..6, siehe Effektliste in der GUI)"'
assert old in s, "main effect help"
s = s.replace(old, 'help="Effekt-Index für --shot (0..13, siehe Effektliste in der GUI)"', 1)
io.open(p, "w", encoding="utf-8").write(s)
print("main.py OK")

# ---- tests: Effekt-Registry robuster + neue Effekte ----
p = "tests/test_library.py"
s = io.open(p, encoding="utf-8").read()
old = '''    def test_mvp_effects(self):
        reg = EffectRegistry()
        self.assertEqual(len(reg), len(EFFECTS_MVP))  # 7 Effekte (v0.6.0)
        self.assertEqual(reg.get(0)["id"], "reactive_bg")
        self.assertEqual(reg.get(4)["id"], "clip_wobble")
        self.assertEqual(reg.by_id("beat_ring")["kind"], "ring")
        self.assertEqual(reg.by_id("clip_distort")["clip_kind"], "video")
        self.assertEqual(reg.get(len(EFFECTS_MVP))["id"], "reactive_bg")  # wrap
        # alle clip_-Effekte haben ein clip_kind
        for e in EFFECTS_MVP:
            if e["kind"].startswith("clip_"):
                self.assertIn(e["clip_kind"], ("video", "image"))'''
new = '''    def test_mvp_effects(self):
        reg = EffectRegistry()
        self.assertEqual(len(reg), len(EFFECTS_MVP))  # 14 Effekte (v0.8.0)
        self.assertGreaterEqual(len(EFFECTS_MVP), 14)
        self.assertEqual(reg.get(0)["id"], "reactive_bg")
        self.assertEqual(reg.get(4)["id"], "clip_wobble")
        self.assertEqual(reg.by_id("beat_ring")["kind"], "ring")
        self.assertEqual(reg.by_id("clip_distort")["clip_kind"], "video")
        self.assertEqual(reg.get(len(EFFECTS_MVP))["id"], "reactive_bg")  # wrap
        # ids eindeutig, kinds gültig
        ids = [e["id"] for e in EFFECTS_MVP]
        self.assertEqual(len(ids), len(set(ids)))
        for e in EFFECTS_MVP:
            if e["kind"].startswith("clip_"):
                self.assertIn(e["clip_kind"], ("video", "image"))
            else:
                self.assertIn(e["kind"], ("bg", "ring"))
        # neue generative Modi (v0.8.0) vorhanden und eindeutig
        bg_modes = [e["mode"] for e in EFFECTS_MVP if e["kind"] == "bg"]
        self.assertEqual(sorted(bg_modes), [0, 1, 2, 3, 4])
        for eid in ("sunburst", "tunnel", "plasma", "kaleido", "clip_glitch", "clip_pixel", "clip_invert"):
            self.assertIn(eid, ids)'''
assert old in s, "test effects"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("tests OK")
