#version 330
// Generativer Hintergrund: Bass treibt Wellen, Beat-Envelope pulst, Mid/High färben.
uniform vec2 u_res;
uniform float u_time, u_beat_phase, u_beat_env, u_bass, u_mid, u_high, u_kick;
out vec4 frag;

void main() {
    vec2 uv = gl_FragCoord.xy / u_res;
    vec2 c = uv - 0.5;
    c.x *= u_res.x / u_res.y;
    float r = length(c);
    // Bass-Wellen
    float wave = sin(r * 40.0 - u_time * (2.0 + 8.0 * u_bass) + u_mid * 6.0) * 0.5 + 0.5;
    wave *= exp(-r * (3.0 - 2.0 * u_bass));
    // Beat-Puls von innen (u_beat_phase für feine Modulation innerhalb des Beats)
    float pulse = u_beat_env * exp(-r * 6.0) * (0.85 + 0.15 * sin(u_beat_phase * 6.2831));
    vec3 col = vec3(0.02, 0.02, 0.05)
             + vec3(0.1, 0.3, 0.9) * wave * (0.2 + u_bass)
             + vec3(0.9, 0.2, 0.6) * pulse
             + vec3(0.2, 0.9, 0.4) * u_high * 0.15 * sin(u_time * 3.0 + uv.y * 20.0);
    // leichte Vignette
    col *= 1.0 - smoothstep(0.4, 0.9, r) * 0.6;
    frag = vec4(col, 1.0);
}
