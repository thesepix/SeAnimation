#version 330
// UI-Quad: Textur * Tint (für farbige Flächen: 1x1-Weißtextur mit Tint)
uniform sampler2D u_tex;
uniform vec4 u_tint;
in vec2 v_uv;
out vec4 frag;
void main() {
    vec4 t = texture(u_tex, v_uv);
    frag = vec4(t.rgb * u_tint.rgb, t.a * u_tint.a);
}
