import os
from kivy.graphics.fbo import Fbo
from kivy.graphics import Color, Rectangle, RenderContext

GAUSSIAN_FS = '''
$HEADER$
uniform vec2 texel_size;

void main(void) {
    vec4 sum = vec4(0.0);
    float w[3];
    w[0] = 0.227027;
    w[1] = 0.316216;
    w[2] = 0.070270;

    for (int x = -2; x <= 2; x++) {
        for (int y = -2; y <= 2; y++) {
            vec2 offset = vec2(float(x), float(y)) * texel_size;
            float weight = w[abs(x)] * w[abs(y)];
            sum += texture2D(texture0, tex_coord0 + offset) * weight;
        }
    }
    gl_FragColor = sum;
}
'''

class GradientBlur:
    def __init__(self, start_size=1024, steps=5):
        self.fbos = []
        size = start_size
        for i in range(steps):
            size = max(size // 2, 16)
            fbo = Fbo(size=(size, size))
            fbo.texture.mag_filter = 'linear'
            fbo.texture.min_filter = 'linear'
            fbo.shader.fs = GAUSSIAN_FS
            self.fbos.append(fbo)

    def process(self, source_texture):
        current_texture = source_texture
        current_texture.mag_filter = 'linear'
        current_texture.min_filter = 'linear'

        for fbo in self.fbos:
            fbo.clear_buffer()
            with fbo:
                fbo['texel_size'] = (
                    1.0 / current_texture.size[0],
                    1.0 / current_texture.size[1],
                )
                Color(1,1,1,1)
                Rectangle(texture=current_texture, size=fbo.size)
            fbo.draw()
            current_texture = fbo.texture

        return current_texture
