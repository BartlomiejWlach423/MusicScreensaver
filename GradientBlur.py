import os
from kivy.graphics.fbo import Fbo
from kivy.graphics import Color, Rectangle

class GradientBlur:
    def __init__(self, start_size=1024, steps=7):
        self.fbos = []
        size = start_size
        for i in range(steps):
            size = max(size // 2, 4)
            fbo = Fbo(size=(size, size))
            fbo.texture.mag_filter = 'linear'
            fbo.texture.min_filter = 'linear'
            self.fbos.append(fbo)

    def process(self, source_texture):
        current_texture = source_texture
        current_texture.mag_filter = 'linear'
        current_texture.min_filter = 'linear'

        for fbo in self.fbos:
            fbo.clear_buffer()
            with fbo:
                Color(1,1,1,1)
                Rectangle(texture=current_texture, size=fbo.size)
            fbo.draw()
            current_texture = fbo.texture

        return current_texture
