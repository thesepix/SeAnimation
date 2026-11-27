#version 330
// UI-Quad: in_pos in Pixelkoordinaten (y bottom-up, wie pyglet-Maus-Events)
in vec2 in_pos;
in vec2 in_uv;
uniform vec2 u_res;
out vec2 v_uv;
void main() {
    vec2 ndc = in_pos / u_res * 2.0 - 1.0;
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_uv = in_uv;
}
