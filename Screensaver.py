import platform
import os

OPERATING_SYSTEM = platform.system()

from screeninfo import get_monitors

monitors = []

for monitor in get_monitors():
    monitors.append(monitor)

monitors_len = len(monitors)

max_width_res = 500
height_res = 500

if monitors_len>1:
    max_width_res = monitors[0].width
    height_res = monitors[0].height
    for monitor in monitors:
        if monitor.width > max_width_res:
            max_width_res = monitor.width
            height_res = monitor.height

print(f"Screen resolution: {max_width_res}, {height_res}")

from kivy.config import Config
Config.set('graphics', 'width', max_width_res)
Config.set('graphics', 'height', height_res)
Config.set('graphics', 'maxfps', '60')
#Config.set('graphics', 'fullscreen', 'auto')
#Config.getint('kivy', 'show_fps')

from kivy.core.window import Window
Window.clearcolor = (0,0,0,1)

from kivy.clock import Clock
from kivy.clock import mainthread

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.metrics import sp, dp
from kivy.uix.widget import Widget
from kivy.graphics.texture import Texture

import math
import asyncio
import threading
import tempfile
import winrt.windows.foundation
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions

async def saveThumbnail(thumb_ref, output_path):
    if thumb_ref is None:
        return None

    stream = await thumb_ref.open_read_async()
    size = stream.size

    if not size:
        return None

    reader = DataReader(stream)
    await reader.load_async(size)

    buffer = bytearray(size)
    reader.read_bytes(buffer)

    with open(output_path, "wb") as f:
        f.write(buffer)

    return output_path

async def getMediaProperties():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    if current_session:
        properties = await current_session.try_get_media_properties_async()

        cover_path = os.path.join(tempfile.gettempdir(), "current_cover.jpg")
        saved_path = await saveThumbnail(properties.thumbnail, cover_path)

        return saved_path, properties.title, properties.artist
    else:
        print("No session")
        return None, "Empty", "Empty"

from kivy.graphics.fbo import Fbo
BLUR_H_SHADER = '''
$HEADER$
uniform vec2 resolution;
uniform float blur_size;

void main(void) {
    vec4 sum = vec4(0.0);
    float dt = blur_size / resolution.x;

    sum += texture2D(texture0, vec2(tex_coord0.x - 6.0*dt, tex_coord0.y)) * 0.002216;
    sum += texture2D(texture0, vec2(tex_coord0.x - 5.0*dt, tex_coord0.y)) * 0.008764;
    sum += texture2D(texture0, vec2(tex_coord0.x - 4.0*dt, tex_coord0.y)) * 0.026995;
    sum += texture2D(texture0, vec2(tex_coord0.x - 3.0*dt, tex_coord0.y)) * 0.064759;
    sum += texture2D(texture0, vec2(tex_coord0.x - 2.0*dt, tex_coord0.y)) * 0.120985;
    sum += texture2D(texture0, vec2(tex_coord0.x - dt,     tex_coord0.y)) * 0.176033;
    sum += texture2D(texture0, vec2(tex_coord0.x,          tex_coord0.y)) * 0.199471;
    sum += texture2D(texture0, vec2(tex_coord0.x + dt,     tex_coord0.y)) * 0.176033;
    sum += texture2D(texture0, vec2(tex_coord0.x + 2.0*dt, tex_coord0.y)) * 0.120985;
    sum += texture2D(texture0, vec2(tex_coord0.x + 3.0*dt, tex_coord0.y)) * 0.064759;
    sum += texture2D(texture0, vec2(tex_coord0.x + 4.0*dt, tex_coord0.y)) * 0.026995;
    sum += texture2D(texture0, vec2(tex_coord0.x + 5.0*dt, tex_coord0.y)) * 0.008764;
    sum += texture2D(texture0, vec2(tex_coord0.x + 6.0*dt, tex_coord0.y)) * 0.002216;

    gl_FragColor = sum;
}
'''

BLUR_V_SHADER = '''
$HEADER$
uniform vec2 resolution;
uniform float blur_size;

void main(void) {
    vec4 sum = vec4(0.0);
    float dt = blur_size / resolution.y;

    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y - 6.0*dt)) * 0.002216;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y - 5.0*dt)) * 0.008764;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y - 4.0*dt)) * 0.026995;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y - 3.0*dt)) * 0.064759;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y - 2.0*dt)) * 0.120985;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y - dt))     * 0.176033;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y))          * 0.199471;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y + dt))     * 0.176033;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y + 2.0*dt)) * 0.120985;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y + 3.0*dt)) * 0.064759;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y + 4.0*dt)) * 0.026995;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y + 5.0*dt)) * 0.008764;
    sum += texture2D(texture0, vec2(tex_coord0.x, tex_coord0.y + 6.0*dt)) * 0.002216;

    gl_FragColor = sum;
}
'''


class GradientBlur:
    def __init__(self, start_size=1024, steps=6):
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
                Rectangle(texture=source_texture, size=fbo.size)
            fbo.draw()
            current_texture = fbo.texture

        return current_texture
    
class AlbumCover(BoxLayout):
    pass

class MusicScreensaver(App):
    def build(self):
        self.cover = None
        self.title = ""
        self.artist = ""
        self.elapsed_time = 0

        self.gradient_blur = GradientBlur(start_size=1024, steps=8)

        #background
        root = FloatLayout()

        with root.canvas.before:
            Color(1,1,1,0.7)
            PushMatrix()
            self.bg_rotation = Rotate(angle=0, origin=root.center)
            self.bg_rect = Rectangle(
                texture=CoreImage("no_cover.jpg").texture,
                size=root.size,
                pos=root.pos
            )
            PopMatrix()
        root.bind(size=self.UpdateBackgroundGeometry, pos=self.UpdateBackgroundGeometry)

        layout = AnchorLayout(anchor_x='center', anchor_y='center')
        
        verticalBox = BoxLayout(orientation="vertical", size_hint=(0.8, 1.0))
        
        #album cover
        coverAnchor = AnchorLayout(anchor_x='center', anchor_y='center', padding=(dp(40)))
        self.albumCover = Image(keep_ratio=True, allow_stretch=True)
        coverAnchor.add_widget(self.albumCover)
        verticalBox.add_widget(coverAnchor)

        #label with title And artist
        self.titleArtistLabel = Label(text=self.title, color=(1,1,1,1), bold=True, font_size=sp(65), size_hint=(1.0, 0.1))
        verticalBox.add_widget(self.titleArtistLabel)

        layout.add_widget(verticalBox)

        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self.StartMetadataUpdateLoop, daemon=True).start()
        Clock.schedule_interval(self.TriggerMetadataUpdate, 1.0)
        Clock.schedule_interval(self.Animate, 1/60)

        root.add_widget(layout)
        return root

    def Animate(self, dt):
        self.elapsed_time += dt/40
        value = math.sin(self.elapsed_time)*360
        self.bg_rotation.angle = value
        print(value)

    def ScaleBackground(self, zoom=1.2):
        texture = self.bg_rect.texture
        if texture is None:
            return

        tex_ratio = texture.width / texture.height
        target_w, target_h = self.root_size
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

    def StartMetadataUpdateLoop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def TriggerMetadataUpdate(self, dt):
        asyncio.run_coroutine_threadsafe(self.UpdateMetadata(), self._loop)

    async def UpdateMetadata(self):
        thumbnail_path, title, raw_artist = await getMediaProperties()
        artist, _, _ = raw_artist.partition(' — ')
        self.ApplyMetadata(thumbnail_path, title, artist)
        print(f"[GetMediaProperties]: {thumbnail_path}, {title}, {artist}")

    @mainthread
    def ApplyMetadata(self, thumb_path, title, artist):
        self.title = title
        self.artist = artist
        self.titleArtistLabel.text = f"{title} — {artist}" if artist and title else title

        if thumb_path:
            self.albumCover.source = thumb_path
            self.albumCover.reload()

            self.UpdateBackgroundImage(thumb_path)
        else:
            self.albumCover.source = "no_cover.jpg"
            self.UpdateBackgroundImage("no_cover.jpg")

    def StopMetadataUpdate(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

if __name__ == "__main__":
    if OPERATING_SYSTEM == "Windows":
        MusicScreensaver().run()
    else:
        print("System does not match requirements")