
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader
import tempfile
import itertools
import os

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

    outputPath = os.path.join(output_dir, f"cover_{next(_thumb_counter)}.jpg")
    with open(outputPath, "wb") as f:
        f.write(buffer)

    return outputPath

async def GetCurrentSession():
    sessions = await MediaManager.request_async()
    return sessions.get_current_session()

async def GetMediaProperties():
    currentSession = await GetCurrentSession()
    if currentSession:
        properties = await currentSession.try_get_media_properties_async()

        savedPath = await SaveThumbnail(properties.thumbnail, tempfile.gettempdir())

        return savedPath, properties.title, properties.artist
    else:
        print("No session")
        return None, "Empty", ""

async def SkipNext():
    currentSession = await GetCurrentSession()
    if currentSession:
        return await currentSession.try_skip_next_async()
    return False

async def SkipPrevious():
    currentSession = await GetCurrentSession()
    if currentSession:
        return await currentSession.try_skip_previous_async()
    return False

async def Pause():
    currentSession = await GetCurrentSession()
    if currentSession:
        return await currentSession.try_toggle_play_pause_async()
    return False

from pycaw.pycaw import AudioUtilities

volumeInterface = None

def GetVolumeInterface():
    global volumeInterface
    if volumeInterface is None:
        devices = AudioUtilities.GetSpeakers()
        volumeInterface = devices.EndpointVolume
    return volumeInterface

def SetVolume(step=0.05):
    volume = GetVolumeInterface()
    currentVol = volume.GetMasterVolumeLevelScalar()
    newVol = max(0.0, min(1.0, currentVol + step))
    volume.SetMasterVolumeLevelScalar(newVol, None)
    return newVol

class MediaSessionListener:
    def __init__(self, on_change):
        self.onChange = on_change
        self.manager = None
        self.currentSession = None
        self.sessionChanged = None
        self.propertiesToken = None
        self.playbackToken = None

    async def Start(self):
        self.manager = await MediaManager.request_async()
        self.sessionChanged = self.manager.add_current_session_changed(
            self.OnCurrentSessionChanged
        )
        self.AttachToSession(self.manager.get_current_session())

    def Stop(self):
        if self.manager is not None and self.sessionChanged is not None:
            try:
                self.manager.remove_current_session_changed(self.sessionChanged)
            except Exception:
                print("[MediaSessionListener] stop error")
        self.DetachFromSession()
        self.manager = None

    def OnCurrentSessionChanged(self, manager, args):
        self.AttachToSession(manager.get_current_session())

    def AttachToSession(self, session):
        self.DetachFromSession()
        self.currentSession = session

        if session is not None:
            try:
                self.propertiesToken = session.add_media_properties_changed(
                    self.OnMediaPropertiesChanged
                )
                self.playbackToken = session.add_playback_info_changed(
                    self.OnPlaybackInfoChanged
                )
            except Exception as e:
                print(f"[MediaSessionListener] attach to session error: {e}")

        self.onChange()

    def DetachFromSession(self):
        if self.currentSession is not None:
            try:
                if self.propertiesToken is not None:
                    self.currentSession.remove_media_properties_changed(self.propertiesToken)
                if self.playbackToken is not None:
                    self.currentSession.remove_playback_info_changed(self.playbackToken)
            except Exception as e:
                print(f"[MediaSessionListener] detach from session error: {e}")

        self.currentSession = None
        self.propertiesToken = None
        self.playbackToken = None

    def OnMediaPropertiesChanged(self, session, args):
        print("[MediaSessionListener] change event")
        self.onChange()

    def OnPlaybackInfoChanged(self, session, args):
        print("[MediaSessionListener] playback info changed")
        self.onChange()