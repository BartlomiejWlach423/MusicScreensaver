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

from AlbumCover import AlbumCover
from AudioPulseMonitor import AudioPulseMonitor
from ShadowLabel import ShadowLabel
from SpringStep import SpringStep
from Utils import ResourcePath
from MediaSession import GetMediaProperties
from AsyncManager import GetLoop
from BlurredBackground import BlurredBackground
from MediaSession import SkipNext, SkipPrevious, Pause, SetVolume
 
class MusicScreensaver(App):
    def build(self):
        self.cover = None
        self.title = ""
        self.artist = ""
        self.lastThumbPath = None
        self.targetPulse = 1.0
        self._pulse_velocity = 0.0

        root = FloatLayout()

        self._keyboard = Window.request_keyboard(self.OnKeyboardClosed, root)
        self._keyboard.bind(on_key_down=self.OnKeyDown)

        #background with blur effect
        self.blurredBackground = BlurredBackground()
        root.add_widget(self.blurredBackground)
        self.blurredBackground.UpdateBackgroundImage(ResourcePath("no_cover.jpg"))
        
        #main layout
        verticalBox = BoxLayout(orientation="vertical", size_hint=(1.0, 1.0))
        
        #album cover
        coverAnchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1.0, 1))
        
        self.albumCover = AlbumCover(source=ResourcePath("no_cover.jpg"), radius_ratio=0.07, size_hint=(None, None), allow_stretch=True, keep_ratio=True)
        self.audioMonitor = AudioPulseMonitor(callback=self.OnAudioPulse, bass_cutoff_hz=150)
        self.audioMonitor.start()

        coverAnchor.add_widget(self.albumCover)
        verticalBox.add_widget(coverAnchor)

        #label with title And artist
        titleArtistAnchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1.0, 0.1))

        self.titleArtistLabel = ShadowLabel(text=self.title, color=(1,1,1,1), bold=True, font_size=sp(60), size_hint=(None, None))

        titleArtistAnchor.add_widget(self.titleArtistLabel)
        verticalBox.add_widget(titleArtistAnchor)

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
            self.targetPulse,
            stiffness,
            damping,
            dt,
        )

        self.blurredBackground.Animate(dt, self.albumCover.pulse_scale)
    
    def StartMetadataUpdateLoop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def TriggerMetadataUpdate(self, dt):
        GetLoop().Run(self.UpdateMetadata())

    async def UpdateMetadata(self):
        thumbnailPath, title, rawArtist = await GetMediaProperties()
        artist, _, _ = rawArtist.partition(' — ')

        if thumbnailPath == self.lastThumbPath and title == self.title:
            if thumbnailPath and thumbnailPath != self.lastThumbPath:
                self.CleanupOldThumb(thumbnailPath)

        self.ApplyMetadata(thumbnailPath, title, artist)

    def CleanupOldThumb(self, keep_path):
        old_path = self.lastThumbPath
        self.lastThumbPath = keep_path
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

                self.blurredBackground.UpdateBackgroundImage(thumb_path)
            else:
                self.albumCover.source = ResourcePath("no_cover.jpg")
                self.blurredBackground.UpdateBackgroundImage(ResourcePath("no_cover.jpg"))
        except Exception as e:
            import traceback
            print(f"Album cover loading error: {e}")
            traceback.print_exc()
            self.albumCover.source = ResourcePath("no_cover.jpg")
            self.blurredBackground.UpdateBackgroundImage(ResourcePath("no_cover.jpg"))

        self.CleanupOldThumb(thumb_path)

    def StopMetadataUpdate(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

    @mainthread
    def OnAudioPulse(self, pulse_value):
        self.targetPulse = pulse_value
        #print(f"Pulse = {pulse_value:.4f}")

    def on_stop(self):
        self.audioMonitor.stop()
        GetLoop().Stop()

    def OnKeyboardClosed(self):
        self._keyboard.unbind(on_key_down=self.OnKeyDown)
        self._keyboard = None

    def OnKeyDown(self, window, keycode, scancode, codepoint):
        key = keycode[1]

        if key == 'spacebar':
            self.OnSpacePressed()
        elif key == 'left':
            self.OnLeftArrowPressed()
        elif key == 'right':
            self.OnRightArrowPressed()
        elif key == 'down':
            self.OnUpDownArrowPressed(step=-0.05)
        elif key == 'up':
            self.OnUpDownArrowPressed(step=0.05)
        else:
            self.OnAnythingElsePressed()

        return True

    def OnAnythingElsePressed(self):
        self.stop()

    def OnUpDownArrowPressed(self, step):
        SetVolume(step=step)

    def OnSpacePressed(self):
        GetLoop().Run(Pause())

    def OnLeftArrowPressed(self):
        GetLoop().Run(SkipPrevious())

    def OnRightArrowPressed(self):
        GetLoop().Run(SkipNext())

if __name__ == "__main__":
    if OPERATING_SYSTEM == "Windows":
        MusicScreensaver().run()
    else:
        print("System does not match requirements")