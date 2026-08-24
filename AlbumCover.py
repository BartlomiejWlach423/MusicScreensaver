from kivy.graphics import Color, Scale, Rectangle, PushMatrix, PopMatrix,  StencilPush, StencilUse, StencilUnUse, StencilPop, RoundedRectangle, BoxShadow
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget

class AlbumCover(Widget):
    source = StringProperty("")
    radius_ratio = NumericProperty(0.05)
    allow_stretch = BooleanProperty(True)
    keep_ratio = BooleanProperty(False)
    pulse_scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.image = Image(
            source=self.source,
            allow_stretch=self.allow_stretch,
            keep_ratio=self.keep_ratio,
            pos=self.pos,
            size=self.size,
        )
        self.add_widget(self.image)

        with self.canvas.before:
            self.shadow_color = Color(0, 0, 0, 0.5)
            self.shadow = BoxShadow(
                pos=self.pos,
                size=self.size,
                offset=(0, -10),
                spread_radius=(-5, -5),
                border_radius=(20, 20, 20, 20),
                blur_radius=100,
            )
            PushMatrix()
            self.scale_instr = Scale(1.0, 1.0, 1.0)
            StencilPush()
            self.mask = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[1],
            )
            StencilUse()

        with self.canvas.after:
            StencilUnUse()
            self.mask_pop = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[1],
            )
            StencilPop()
            PopMatrix()

        self.bind(
            pos=self.UpdateCanvas,
            size=self.UpdateCanvas,
            radius_ratio=self.UpdateCanvas,
            source=self.UpdateSource,
            allow_stretch=self.UpdateAllowStretch,
            keep_ratio=self.UpdateKeepRatio,
            pulse_scale=self.UpdatePulse,
        )

        self.UpdateCanvas()
        self.bind(parent=self.BindToParent)

    def BindToParent(self, _, parent):
        if parent:
            parent.bind(size=self.FitSquareToParent)
            self.FitSquareToParent(parent, parent.size)

    def FitSquareToParent(self, parent, parent_size, margin_ratio=0.95):
        side = min(parent_size) * margin_ratio
        self.size = (side, side)

    def reload(self):
        self.image.reload()

    def UpdateCanvas(self, *_):
        computed_radius = max(min(self.size) * self.radius_ratio, 1)

        self.mask.pos = self.pos
        self.mask.size = self.size
        self.mask.radius = [computed_radius]

        self.mask_pop.pos = self.pos
        self.mask_pop.size = self.size
        self.mask_pop.radius = [computed_radius]

        self.image.pos = self.pos
        self.image.size = self.size

        self.shadow.pos = self.pos
        self.shadow.size = self.size
        r = self.radius_ratio * min(self.size)
        self.shadow.border_radius = (r, r, r, r)

    def UpdateSource(self, _, source):
        self.image.source = source

    def UpdateAllowStretch(self, _, value):
        self.image.allow_stretch = value

    def UpdateKeepRatio(self, _, value):
        self.image.keep_ratio = value

    def UpdatePulse(self, *_):
        self.scale_instr.x = self.pulse_scale
        self.scale_instr.y = self.pulse_scale
        self.scale_instr.origin = self.center

        intensity = min((self.pulse_scale - 1.0) * 5, 0.7)
        self.shadow_color = (0, 0, 0, 0.3 + intensity)
        self.shadow.blur_radius = 100 + (self.pulse_scale - 1.0) * 400