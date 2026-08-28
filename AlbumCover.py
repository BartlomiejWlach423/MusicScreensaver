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
    pulse_range = NumericProperty(0.08)
    base_blur_radius = NumericProperty(150)
    base_spread = NumericProperty(-8)
    base_alpha = NumericProperty(0.75)
    pulse_blur_boost = NumericProperty(200)
    pulse_spread_boost = NumericProperty(40)
    pulse_alpha_boost = NumericProperty(0.25)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bindedParent = None

        self.image = Image(
            source=self.source,
            allow_stretch=self.allow_stretch,
            keep_ratio=self.keep_ratio,
            pos=self.pos,
            size=self.size,
        )
        self.add_widget(self.image)

        with self.canvas.before:
            self.shadow_color = Color(0, 0, 0, self.base_alpha)
            self.shadow = BoxShadow(
                pos=self.pos,
                size=self.size,
                offset=(0, -10),
                spread_radius=(self.base_spread, self.base_spread),
                border_radius=(20, 20, 20, 20),
                blur_radius=self.base_blur_radius,
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
        self.UpdatePulse()
        self.bind(parent=self.BindToParent)

    def BindToParent(self, _, parent):
        if self.bindedParent is not None:
            try:
                self.bindedParent.unbind(self.FitSquareToParent)
            except Exception:
                print("[AlbumCover] parent unbinding error")
            self.bindedParent = None

        if parent:
            parent.bind(size=self.FitSquareToParent)
            self.FitSquareToParent(parent, parent.size)

    def FitSquareToParent(self, parent, parent_size, margin_ratio=0.7):
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
        raw_excess = max(self.pulse_scale - 1.0, 0.0)
        intensity = min(raw_excess / self.pulse_range, 1.0) if self.pulse_range > 0 else 0.0

        spread = self.base_spread - intensity * self.pulse_spread_boost

        self.shadow.spread_radius = (spread, spread)
        self.shadow_color.a = min(self.base_alpha + intensity * self.pulse_alpha_boost, 1.0)
        self.shadow.blur_radius = self.base_blur_radius + intensity * self.pulse_blur_boost