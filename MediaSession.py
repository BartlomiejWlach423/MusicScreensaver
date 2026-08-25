
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
