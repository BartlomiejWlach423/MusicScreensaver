from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate,  StencilPush, StencilUse, StencilUnUse, StencilPop, RoundedRectangle
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget

class AlbumCover(Widget):
    source = StringProperty("")
    radius_ratio = NumericProperty(0.05)
    allow_stretch = BooleanProperty(True)
    keep_ratio = BooleanProperty(False)

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

        self.bind(
            pos=self.UpdateCanvas,
            size=self.UpdateCanvas,
            radius_ratio=self.UpdateCanvas,
            source=self.UpdateSource,
            allow_stretch=self.UpdateAllowStretch,
            keep_ratio=self.UpdateKeepRatio,
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

    def UpdateSource(self, _, source):
        self.image.source = source

    def UpdateAllowStretch(self, _, value):
        self.image.allow_stretch = value

    def UpdateKeepRatio(self, _, value):
        self.image.keep_ratio = value