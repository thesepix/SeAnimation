#version 330
// Clip-Layer: Textur-Sampling mit optionalem Kugel-Wobble (u_wobble) und Kick-Puls (u_kick).
uniform sampler2D u_tex;
uniform vec2 u_res;
uniform float u_time, u_beat_phase, u_beat_env, u_wobble, u_kick, u_pulse;
out vec4 frag;

void main() {
    vec2 uv = gl_FragCoord.xy / u_res;
    vec2 c = uv - 0.5;
    // Kick-Puls: kurzes Zoomen auf dem Beat
    float zoom = 1.0 + u_pulse * u_kick * 0.12;
    c /= zoom;
    // Kugel-Wobble: UVs auf Kugel projizieren, Radius wackelt mit Beat-Envelope
    if (u_wobble > 0.001) {
        float wob = u_wobble * u_beat_env * 0.25;
        float r = length(c) * (1.0 + wob * sin(u_time * 10.0));
        float z = sqrt(max(0.0, 1.0 - r * r));
        vec2 suv = c * (2.0 / max(0.6, 1.0 + z)) * 0.5 + 0.5;  // Kugel-Projektion
        suv = clamp(suv, 0.001, 0.999);
        frag = texture(u_tex, suv);
        // Kugelrand abdunkeln
        frag.rgb *= smoothstep(1.0, 0.7, r);
    } else {
        frag = texture(u_tex, clamp(c + 0.5, 0.001, 0.999));
    }
}
