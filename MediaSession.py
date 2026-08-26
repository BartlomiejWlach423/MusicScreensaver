
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

async def GetMediaProperties():
    sessions = await MediaManager.request_async()
    currentSession = sessions.get_current_session()
    if currentSession:
        properties = await currentSession.try_get_media_properties_async()

        savedPath = await SaveThumbnail(properties.thumbnail, tempfile.gettempdir())

        return savedPath, properties.title, properties.artist
    else:
        print("No session")
        return None, "Empty", ""

async def SkipNext():
    sessions = await MediaManager.request_async()
    currentSession = sessions.get_current_session()
    if currentSession:
        return await currentSession.try_skip_next_async()
    return False

async def SkipPrevious():
    sessions = await MediaManager.request_async()
    currentSession = sessions.get_current_session()
    if currentSession:
        return await currentSession.try_skip_previous_async()
    return False

async def Pause():
    sessions = await MediaManager.request_async()
    currentSession = sessions.get_current_session()
    currentSession.try_g
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
