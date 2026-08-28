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
from MediaSession import SkipNext, SkipPrevious, Pause, SetVolume, MediaSessionListener
 
class MusicScreensaver(App):
    def build(self):
        self.cover = None
        self.title = ""
        self.artist = ""
        self.lastThumbPath = None
        self.targetPulse = 1.0
        self.pulseVelocity = 0.0
        self.updatingMetadata = False

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
        
        self.albumCover = AlbumCover(source=ResourcePath("no_cover.jpg"), radius_ratio=0.1, size_hint=(None, None), allow_stretch=True, keep_ratio=True)
        self.audioMonitor = AudioPulseMonitor(callback=self.OnAudioPulse)
        self.audioMonitor.start()

        coverAnchor.add_widget(self.albumCover)
        verticalBox.add_widget(coverAnchor)

        #label with title And artist
        titleArtistAnchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1.0, 0.1))

        self.titleArtistLabel = ShadowLabel(text=self.title, color=(1,1,1,1), bold=True, font_size=sp(45), size_hint=(None, None))

        titleArtistAnchor.add_widget(self.titleArtistLabel)
        verticalBox.add_widget(titleArtistAnchor)

        self.mediaSessionListener = MediaSessionListener(on_change=self.TriggerMetadataUpdate)
        GetLoop().Run(self.mediaSessionListener.Start())

        #in case of MediaSessionListener fail
        Clock.schedule_interval(self.TriggerMetadataUpdate, 10.0)
        Clock.schedule_interval(self.Animate, 1/60)

        root.add_widget(verticalBox)
        return root

    def Animate(self, dt):
        dt = min(dt, 1/30)
        stiffness = 25.0
        damping = 10.0

        self.albumCover.pulse_scale, self.pulseVelocity = SpringStep(
            self.albumCover.pulse_scale,
            self.pulseVelocity,
            self.targetPulse,
            stiffness,
            damping,
            dt,
        )

        self.blurredBackground.Animate(dt, self.albumCover.pulse_scale)
    
    def TriggerMetadataUpdate(self, *args):
        GetLoop().Run(self.UpdateMetadata())

    async def UpdateMetadata(self):
        if self.updatingMetadata:
            return
        self.updatingMetadata = True
        try:
            thumbnailPath, title, rawArtist = await GetMediaProperties()
            noSession = title is None

            if noSession:
                title = ""
                artist = ""
            else:
                artist, _, _ = rawArtist.partition(' — ')

            if thumbnailPath == self.lastThumbPath and title == self.title and artist == self.artist:
                return

            self.ApplyMetadata(thumbnailPath, title, artist, no_session=noSession)
        finally:
            self.updatingMetadata = False

    def CleanupOldThumb(self, keep_path):
        oldPath = self.lastThumbPath
        self.lastThumbPath = keep_path
        if oldPath and oldPath != keep_path and os.path.exists(oldPath):
            try:
                os.remove(oldPath)
            except OSError:
                pass

    @mainthread
    def ApplyMetadata(self, thumb_path, title, artist, no_session=False):
        self.title = title
        self.artist = artist
        self.titleArtistLabel.text = f"{title} — {artist}" if artist and title else title

        if thumb_path:
            try:
                self.albumCover.source = thumb_path
                self.albumCover.reload()
                self.blurredBackground.UpdateBackgroundImage(thumb_path)
            except Exception as e:
                import traceback
                print(f"Album cover loading error: {e}")
                traceback.print_exc()
                thumb_path = ResourcePath("no_cover.jpg")
                self.albumCover.source = thumb_path
                self.blurredBackground.UpdateBackgroundImage(thumb_path)
                
            self.CleanupOldThumb(thumb_path)
        elif no_session:
            placeholder = ResourcePath("no_cover.jpg")
            self.albumCover.source = placeholder
            self.blurredBackground.UpdateBackgroundImage(placeholder)
            self.CleanupOldThumb(None)

    @mainthread
    def OnAudioPulse(self, pulse_value):
        self.targetPulse = pulse_value

    def on_stop(self):
        self.audioMonitor.Stop()
        self.mediaSessionListener.Stop()
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