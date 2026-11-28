#version 330
// Generativer Hintergrund — mehrere Modi (u_mode), alle musik-reaktiv:
//   0 Bass-Wellen (klassisch), 1 Sonnenstrahlen, 2 Tunnel-Zoom, 3 Plasma, 4 Kaleidoskop
// Beat-Envelope (u_beat_env) und Phase (u_beat_phase) treiben jeden Modus im Takt.
uniform vec2 u_res;
uniform float u_time, u_beat_phase, u_beat_env, u_bass, u_mid, u_high, u_kick, u_mode;
out vec4 frag;

vec3 pal(float t) {
    return 0.5 + 0.5 * cos(6.28318 * (t + vec3(0.0, 0.33, 0.67)));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_res;
    vec2 c = uv - 0.5;
    c.x *= u_res.x / u_res.y;
    float r = length(c);
    float ang = atan(c.y, c.x);
    int m = int(u_mode + 0.5);
    float pulse = u_beat_env * (0.85 + 0.15 * sin(u_beat_phase * 6.28318));
    vec3 col = vec3(0.02, 0.02, 0.05);

    if (m == 1) {
        // Sonnenstrahlen: rotierende Strahlen; Bass = mehr/wilder, Beat pulsiert
        float rays = 0.5 + 0.5 * sin(ang * (8.0 + 6.0 * u_bass) + u_time * (0.6 + 1.5 * pulse));
        rays *= exp(-r * 2.5);
        col += pal(0.3 + u_time * 0.05 + r * 0.5) * rays * (0.3 + u_bass + 0.8 * pulse);
    } else if (m == 2) {
        // Tunnel: konzentrische Ringe zoomen auf den Beat zu
        float z = fract(r * 5.0 - u_time * (0.4 + 1.2 * u_beat_env));
        float ring = smoothstep(0.0, 0.15, z) * smoothstep(1.0, 0.6, z);
        float spokes = 0.5 + 0.5 * sin(ang * 12.0 + r * 8.0 - u_time * 2.0);
        col += pal(z * 0.8 + u_time * 0.03) * ring * (0.4 + spokes * 0.6) * (0.5 + u_kick + 0.6 * pulse);
        col *= 1.0 - smoothstep(0.7, 1.1, r) * 0.7;
    } else if (m == 3) {
        // Plasma: klassisches Sinus-Feld; Beat verzerrt, Hue driftet
        float t = u_time * (1.0 + 2.0 * u_beat_env);
        float v = sin(uv.x * 10.0 + t) + sin(uv.y * 8.0 - t * 1.3)
                + sin((uv.x + uv.y) * 6.0 + t) + sin(r * 14.0 - t * 2.0) + u_bass * 2.0;
        v /= 5.0;
        col += pal(v * 0.5 + u_time * 0.05 + u_mid * 0.2) * (0.35 + 0.4 * pulse) * (0.6 + 0.4 * u_high);
    } else if (m == 4) {
        // Kaleidoskop: gespiegelt gefaltete Segmente, rotieren langsam
        float a = mod(ang + u_time * 0.15, 6.28318 / 6.0);
        a = abs(a - 3.14159 / 6.0);
        vec2 kc = vec2(cos(a), sin(a)) * r;
        float pat = sin(kc.x * 20.0 + u_time) * sin(kc.y * 20.0 - u_time * 1.2);
        col += pal(pat * 0.3 + r + u_time * 0.04) * (0.25 + 0.5 * u_bass + 0.5 * pulse);
        col *= exp(-r * 1.5);
    } else {
        // Modus 0: Bass-Wellen
        float wave = sin(r * 40.0 - u_time * (2.0 + 8.0 * u_bass) + u_mid * 6.0) * 0.5 + 0.5;
        wave *= exp(-r * (3.0 - 2.0 * u_bass));
        col += vec3(0.1, 0.3, 0.9) * wave * (0.2 + u_bass)
             + vec3(0.9, 0.2, 0.6) * pulse * exp(-r * 6.0)
             + vec3(0.2, 0.9, 0.4) * u_high * 0.15 * sin(u_time * 3.0 + uv.y * 20.0);
    }

    // leichte Vignette
    col *= 1.0 - smoothstep(0.4, 0.9, r) * 0.6;
    frag = vec4(col, 1.0);
}
