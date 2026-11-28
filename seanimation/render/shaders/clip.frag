#version 330
// Clip-Layer: Textur-Sampling mit Effekten, alle skaliert über Beat-Envelope/Phase:
// u_wobble (Kugel), u_pulse (Kick-Zoom), u_distort (Bass-Warp), u_split (RGB-Split),
// u_glitch (Beat-Slices), u_pixel (Pixel-Puls), u_invert (Kick-Invert-Flash).
uniform sampler2D u_tex;
uniform vec2 u_res;
uniform float u_time, u_beat_phase, u_beat_env, u_bass, u_kick;
uniform float u_wobble, u_pulse, u_distort, u_split, u_glitch, u_pixel, u_invert;
out vec4 frag;

void main() {
    vec2 uv = gl_FragCoord.xy / u_res;
    vec2 c = uv - 0.5;
    c.x *= u_res.x / u_res.y;
    // Kick-Puls: kurzes Zoomen auf dem Beat
    float zoom = 1.0 + u_pulse * u_kick * 0.12;
    c /= zoom;
    // Bass-Warp: UVs wellenförmig verzerren (Bass-Amplitude)
    if (u_distort > 0.001) {
        float w = sin(uv.y * 30.0 + u_time * 4.0) * 0.02 * u_bass * u_distort
                + sin(uv.x * 22.0 - u_time * 3.0) * 0.015 * u_bass * u_distort;
        c.x += w;
    }
    if (u_wobble > 0.001) {
        // Kugel-Wobble: UVs auf Kugel projizieren, Radius wackelt mit Beat-Envelope
        float wob = u_wobble * u_beat_env * (0.2 + 0.05 * sin(u_beat_phase * 6.2831));
        float r = length(c) * (1.0 + wob * sin(u_time * 10.0));
        float z = sqrt(max(0.0, 1.0 - r * r));
        vec2 suv = clamp(c * (2.0 / max(0.6, 1.0 + z)) * 0.5 + 0.5, 0.001, 0.999);
        vec4 col = texture(u_tex, suv);
        col.rgb *= smoothstep(1.0, 0.7, r);  // Kugelrand abdunkeln
        frag = col;
        return;
    }
    vec2 suv = clamp(c + 0.5, 0.001, 0.999);
    // Pixel-Puls: auf dem Beat werden die Pixel größer (Quantisierung der UVs)
    if (u_pixel > 0.001) {
        float px = mix(2.0, 28.0, clamp(u_pixel * u_beat_env, 0.0, 1.0));
        vec2 grid = u_res / px;
        suv = (floor(suv * grid) + 0.5) / grid;
    }
    // Glitch: horizontale Slices verschieben sich auf dem Beat (Zufall pro Zeile+Frame)
    if (u_glitch > 0.001) {
        float row = floor(suv.y * 24.0);
        float h = fract(sin(row * 12.9898 + floor(u_time * 24.0) * 78.233) * 43758.5453);
        float amp = u_glitch * u_beat_env * 0.08 * step(0.5, h);
        suv.x += (h - 0.5) * 2.0 * amp;
    }
    suv = clamp(suv, 0.001, 0.999);
    // RGB-Split (chromatische Aberration), skaliert mit Beat-Envelope
    float s = u_split * u_beat_env * 0.02;
    vec4 col;
    if (u_split > 0.001) {
        col = vec4(
            texture(u_tex, clamp(suv + vec2(s, 0.0), 0.001, 0.999)).r,
            texture(u_tex, suv).g,
            texture(u_tex, clamp(suv - vec2(s, 0.0), 0.001, 0.999)).b,
            1.0);
    } else {
        col = texture(u_tex, suv);
    }
    // Invert-Flash: Kick invertiert kurz die Farben
    if (u_invert > 0.001) {
        col.rgb = mix(col.rgb, 1.0 - col.rgb, clamp(u_invert * u_kick * 1.5, 0.0, 1.0));
    }
    frag = col;
}
