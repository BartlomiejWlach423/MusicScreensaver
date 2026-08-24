import platform
import os

OPERATING_SYSTEM = platform.system()

from MonitorAndScreenManager import DetectAndSetupMonitor

DetectAndSetupMonitor()

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

import sys
import math
import asyncio
import threading
import tempfile
import winrt.windows.foundation
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions

from AlbumCover import AlbumCover
from GradientBlur import GradientBlur

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

import itertools

_thumb_counter = itertools.count()

async def SaveThumbnail(thumb_ref, output_dir):
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

    output_path = os.path.join(output_dir, f"cover_{next(_thumb_counter)}.jpg")
    with open(output_path, "wb") as f:
        f.write(buffer)

    return output_path

async def GetMediaProperties():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    if current_session:
        properties = await current_session.try_get_media_properties_async()

        saved_path = await SaveThumbnail(properties.thumbnail, tempfile.gettempdir())

        return saved_path, properties.title, properties.artist
    else:
        print("No session")
        return None, "Empty", ""

    
class MusicScreensaver(App):
    def build(self):
        self.cover = None
        self.title = ""
        self.artist = ""
        self.elapsed_time = 0
        self._last_thumb_path = None

        self.gradient_blur = GradientBlur(start_size=1024, steps=8)

        #background with blur effect
        root = FloatLayout()

        with root.canvas.before:
            Color(1,1,1,0.7)
            PushMatrix()
            self.bg_rotation = Rotate(angle=0, origin=root.center)
            self.bg_rect = Rectangle(
                texture=CoreImage(resource_path("no_cover.jpg")).texture,
                size=root.size,
                pos=root.pos
            )
            PopMatrix()
        root.bind(size=self.UpdateBackgroundGeometry, pos=self.UpdateBackgroundGeometry)

        #layout
        layout = AnchorLayout(anchor_x='center', anchor_y='center')
        verticalBox = BoxLayout(orientation="vertical", size_hint=(0.8, 1.0))
        
        #album cover
        coverAnchor = AnchorLayout(anchor_x='center', anchor_y='center')
        
        self.albumCover = AlbumCover(source=resource_path("no_cover.jpg"), radius_ratio=0.1, size_hint=(None, None), allow_stretch=True, keep_ratio=True)
        with self.albumCover.canvas.after:
            Color(1,1,1,1)

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
        thumbnail_path, title, raw_artist = await GetMediaProperties()
        artist, _, _ = raw_artist.partition(' — ')

        if thumbnail_path == self._last_thumb_path and title == self.title:
            if thumbnail_path and thumbnail_path != self._last_thumb_path:
                self.CleanupOldThumb(thumbnail_path)

        self.ApplyMetadata(thumbnail_path, title, artist)

    def CleanupOldThumb(self, keep_path):
        old_path = self._last_thumb_path
        self._last_thumb_path = keep_path
        if old_path and old_path != keep_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    @mainthread
    def ApplyMetadata(self, thumb_path, title, artist):
        self.title = title
        self.artist = artist
        self.titleArtistLabel.text = f"{title} — {artist}" if artist and title else title

        try:
            if thumb_path:
                self.albumCover.source = thumb_path
                self.albumCover.reload()

                self.UpdateBackgroundImage(thumb_path)
            else:
                self.albumCover.source = resource_path("no_cover.jpg")
                self.UpdateBackgroundImage(resource_path("no_cover.jpg"))
        except Exception as e:
            import traceback
            print(f"Album cover loading error: {e}")
            traceback.print_exc()
            self.albumCover.source = resource_path("no_cover.jpg")
            self.UpdateBackgroundImage(resource_path("no_cover.jpg"))

        self.CleanupOldThumb(thumb_path)

    def StopMetadataUpdate(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

if __name__ == "__main__":
    if OPERATING_SYSTEM == "Windows":
        MusicScreensaver().run()
    else:
        print("System does not match requirements")