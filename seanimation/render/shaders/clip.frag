#version 330
// Clip-Layer: Textur-Sampling mit Effekten, alle skaliert über Beat-Envelope/Phase:
// u_wobble (Kugel), u_pulse (Kick-Zoom), u_distort (Bass-Wellen), u_split (RGB-Split).
uniform sampler2D u_tex;
uniform vec2 u_res;
uniform float u_time, u_beat_phase, u_beat_env, u_bass, u_kick;
uniform float u_wobble, u_pulse, u_distort, u_split;
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
    vec2 suv;
    if (u_wobble > 0.001) {
        // Kugel-Wobble: UVs auf Kugel projizieren, Radius wackelt mit Beat-Envelope
        float wob = u_wobble * u_beat_env * (0.2 + 0.05 * sin(u_beat_phase * 6.2831));
        float r = length(c) * (1.0 + wob * sin(u_time * 10.0));
        float z = sqrt(max(0.0, 1.0 - r * r));
        suv = clamp(c * (2.0 / max(0.6, 1.0 + z)) * 0.5 + 0.5, 0.001, 0.999);
        frag = texture(u_tex, suv);
        frag.rgb *= smoothstep(1.0, 0.7, r);  // Kugelrand abdunkeln
    } else {
        suv = clamp(c + 0.5, 0.001, 0.999);
        // RGB-Split (chromatische Aberration), skaliert mit Beat-Envelope
        float s = u_split * u_beat_env * 0.02;
        frag = vec4(
            texture(u_tex, clamp(suv + vec2(s, 0.0), 0.001, 0.999)).r,
            texture(u_tex, suv).g,
            texture(u_tex, clamp(suv - vec2(s, 0.0), 0.001, 0.999)).b,
            1.0);
    }
}
