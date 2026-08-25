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
from kivy.metrics import sp

import asyncio
import threading

from AlbumCover import AlbumCover
from AudioPulseMonitor import AudioPulseMonitor
from ShadowLabel import ShadowLabel
from SpringStep import SpringStep
from Utils import ResourcePath
from MediaSession import GetMediaProperties
from BlurredBackground import BlurredBackground
 
class MusicScreensaver(App):
    def build(self):
        self.cover = None
        self.title = ""
        self.artist = ""
        self._last_thumb_path = None
        self._target_pulse = 1.0
        self._pulse_velocity = 0.0

        #background with blur effect
        root = FloatLayout()

        self.blurred_background = BlurredBackground()
        root.add_widget(self.blurred_background)
        self.blurred_background.UpdateBackgroundImage(ResourcePath("no_cover.jpg"))
        
        #layout
        verticalBox = BoxLayout(orientation="vertical", size_hint=(1.0, 1.0))
        
        #album cover
        coverAnchor = AnchorLayout(anchor_x='center', anchor_y='center')
        
        self.albumCover = AlbumCover(source=ResourcePath("no_cover.jpg"), radius_ratio=0.07, size_hint=(None, None), allow_stretch=True, keep_ratio=True)
        self.audioMonitor = AudioPulseMonitor(callback=self.OnAudioPulse, bass_cutoff_hz=150)
        self.audioMonitor.start()

        coverAnchor.add_widget(self.albumCover)
        verticalBox.add_widget(coverAnchor)

        #label with title And artist
        titleArtistAnchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1.0, 0.08))

        self.titleArtistLabel = ShadowLabel(text=self.title, color=(1,1,1,1), bold=True, font_size=sp(65), size_hint=(None, None))

        titleArtistAnchor.add_widget(self.titleArtistLabel)
        verticalBox.add_widget(titleArtistAnchor)

        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self.StartMetadataUpdateLoop, daemon=True).start()
        Clock.schedule_interval(self.TriggerMetadataUpdate, 1.0)
        Clock.schedule_interval(self.Animate, 1/60)

        root.add_widget(verticalBox)
        return root

    def Animate(self, dt):
        dt = min(dt, 1/30)
        stiffness = 25.0
        damping = 10.0

        self.albumCover.pulse_scale, self._pulse_velocity = SpringStep(
            self.albumCover.pulse_scale,
            self._pulse_velocity,
            self._target_pulse,
            stiffness,
            damping,
            dt,
        )

        self.blurred_background.Animate(dt, self.albumCover.pulse_scale)

    
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

                self.blurred_background.UpdateBackgroundImage(thumb_path)
            else:
                self.albumCover.source = ResourcePath("no_cover.jpg")
                self.blurred_background.UpdateBackgroundImage(ResourcePath("no_cover.jpg"))
        except Exception as e:
            import traceback
            print(f"Album cover loading error: {e}")
            traceback.print_exc()
            self.albumCover.source = ResourcePath("no_cover.jpg")
            self.blurred_background.UpdateBackgroundImage(ResourcePath("no_cover.jpg"))

        self.CleanupOldThumb(thumb_path)

    def StopMetadataUpdate(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

    @mainthread
    def OnAudioPulse(self, pulse_value):
        self._target_pulse = pulse_value
        print(f"Pulse = {pulse_value:.4f}")

    def on_stop(self):
        self.audioMonitor.stop()
        self.StopMetadataUpdate()

if __name__ == "__main__":
    if OPERATING_SYSTEM == "Windows":
        MusicScreensaver().run()
    else:
        print("System does not match requirements")