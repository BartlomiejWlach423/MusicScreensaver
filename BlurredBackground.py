from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Scale
from kivy.core.image import Image as CoreImage

import math

from GradientBlur import GradientBlur
from Utils import ResourcePath

class BlurredBackground(Widget):
    def __init__(self, blur_start_size=128, blur_steps=4, **kwargs):
        super().__init__(**kwargs)

        self.elapsed_time = 0
        self.gradient_blur = GradientBlur(start_size=blur_start_size, steps=blur_steps)

        with self.canvas.before:
            self.bg_color = Color(1,1,1,0.7)
            PushMatrix()
            self.bg_rotation = Rotate(angle=0, origin=self.center)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            PopMatrix()

        self.bind(size=self.UpdateBackgroundGeometry, pos=self.UpdateBackgroundGeometry)

    def Animate(self, dt, pulse_scale=1.0):
        self.elapsed_time += dt/40
        self.bg_rotation.angle = math.sin(self.elapsed_time)*360
        self.UpdateBackgroundPulse(pulse_scale)

    def UpdateBackgroundPulse(self, pulse_scale):
        intensity = min((pulse_scale - 1.0), 0.5)
        zoom = 1.15 + intensity * 3.0
        self.ScaleBackground(zoom=zoom)
    
    def ScaleBackground(self, zoom=1.1):
        texture = self.bg_rect.texture
        if texture is None:
            return
    
        tex_ratio = texture.width / texture.height
        target_w, target_h = self.size
        target_ratio = target_w / target_h
    
        if tex_ratio > target_ratio:
            new_h = target_h
            new_w = target_h * tex_ratio
        else:
            new_w = target_w
            new_h = target_w / tex_ratio
    
        new_w *= zoom
        new_h *= zoom
    
        self.bg_rect.size = (new_w, new_h)
        self.bg_rect.pos = (
            (target_w - new_w) / 2,
            (target_h - new_h) / 2,
        )
    
    def UpdateBackgroundGeometry(self, instance, value):
        self.root_size = instance.size
        self.bg_rotation.origin = instance.center
        self.ScaleBackground(zoom=1.2)
    
    def UpdateBackgroundImage(self, img_path):
        raw_texture = CoreImage(img_path, nocache=True).texture
        blurred_texture = self.gradient_blur.process(raw_texture)
    
        self.bg_rect.texture = blurred_texture
        self.ScaleBackground(zoom=1.2)
    