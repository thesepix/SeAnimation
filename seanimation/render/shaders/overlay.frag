#version 330
// Overlay: Beat-Ring (leuchtet mit Beat-Envelope auf, Radius pulsiert) + dezenter Kick-Flash.
uniform vec2 u_res;
uniform float u_time, u_beat_env, u_kick, u_strength;
out vec4 frag;

void main() {
    vec2 uv = gl_FragCoord.xy / u_res;
    vec2 c = uv - 0.5;
    c.x *= u_res.x / u_res.y;
    float r = length(c);
    float ring_r = 0.25 + 0.45 * (1.0 - u_beat_env);  // schrumpft Richtung Mitte nach dem Beat
    float ring = smoothstep(0.03, 0.0, abs(r - ring_r));
    vec3 col = vec3(1.0, 0.9, 0.4) * ring * u_beat_env * u_strength;
    col += vec3(1.0) * u_kick * 0.08 * u_strength;  // dezenter Vollbild-Blitz
    frag = vec4(col, 1.0);
}
