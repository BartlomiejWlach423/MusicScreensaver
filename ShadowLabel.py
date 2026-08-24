from kivy.uix.label import Label
from kivy.graphics import Color, BoxShadow
from kivy.properties import NumericProperty
from kivy.metrics import dp

class ShadowLabel(Label):
    shadow_padding = NumericProperty(dp(10))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.shadow_color = Color(0, 0, 0, 0.4)
            self.shadow = BoxShadow(
                pos=self.pos,
                size=self.size,
                offset=(0, 0),
                spread_radius=(0, 0),
                border_radius=(12, 12, 12, 12),
                blur_radius=200,
            )

        self.bind(
            pos=self.UpdateShadow, 
            size=self.UpdateShadow,
            texture_size=self.UpdateShadow,
            shadow_padding=self.UpdateShadow,
            )

    def UpdateShadow(self, *args):
        w = self.texture_size[0] + self.shadow_padding * 2
        h = self.shadow_padding

        self.shadow.size = (w, h)
        self.shadow.pos = (
            self.center_x - w / 2,
            self.center_y - h / 2,
        )