# GLSL-Shader

Hier landen die Shader der MVP-PRs:

- `background.frag` — generativer Hintergrund (Bass/Beat-getriebene Wellen/Partikel)
- `sphere_wobble.frag` — formt das Bild zur Kugel, Wobble über Beat-Envelope
- `post.frag` — Beat-Ring/Blitz-Overlay, Farbwechsel pro Takt

Alle Shader bekommen als Uniforms u. a. `u_beat_phase`, `u_beat_env`,
`u_bass`, `u_mid`, `u_high`, `u_time` (siehe ANFORDERUNGEN.md Abschnitt 3.3).
