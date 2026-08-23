import platform
import os

OPERATING_SYSTEM = platform.system()

from kivy.config import Config
Config.set('graphics', 'width', '3840')
Config.set('graphics', 'height', '2160')
Config.set('graphics', 'maxfps', '60')
#Config.set('graphics', 'fullscreen', 'auto')
#Config.getint('kivy', 'show_fps')

from kivy.clock import Clock
from kivy.clock import mainthread

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color
from kivy.metrics import sp, dp
#///
from kivy.graphics import Color, Rectangle
import random


def debug_outline(widget, color=None):
    if color is None:
        color = (random.random(), random.random(), random.random(), 0.3)

    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(size=widget.size, pos=widget.pos)

    def update_rect(instance, value):
        rect.size = instance.size
        rect.pos = instance.pos

    widget.bind(size=update_rect, pos=update_rect)

#///
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
    
class AlbumCover(BoxLayout):
    pass

class MusicScreensaver(App):
    def build(self):
        self.cover = None
        self.title = ""
        self.artist = ""

        layout = AnchorLayout(anchor_x='center', anchor_y='center')
        #debug_outline(layout)
        verticalBox = BoxLayout(orientation="vertical", size_hint=(0.8, 1.0))
        #debug_outline(verticalBox)
        #album cover
        coverAnchor = AnchorLayout(anchor_x='center', anchor_y='center', padding=(dp(40)))
        #debug_outline(coverAnchor)
        self.albumCover = Image(keep_ratio=True, allow_stretch=True)
        #debug_outline(self.albumCover)
        coverAnchor.add_widget(self.albumCover)
        verticalBox.add_widget(coverAnchor)

        #label with title And artist
        self.titleArtistLabel = Label(text=self.title, color=(1,1,1,1), bold=True, font_size=sp(65), size_hint=(1.0, 0.1))
        #debug_outline(self.titleArtistLabel)
        verticalBox.add_widget(self.titleArtistLabel)

        layout.add_widget(verticalBox)

        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self.StartMetadataUpdateLoop, daemon=True).start()
        Clock.schedule_interval(self.TriggerMetadataUpdate, 1.0)

        return layout

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
        else:
            self.albumCover.source = "no_cover.png"

    def StopMetadataUpdate(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

if __name__ == "__main__":
    if OPERATING_SYSTEM == "Windows":
        MusicScreensaver().run()
    else:
        print("System does not match requirements")