import asyncio
import threading

class AsyncManager:
    _instance = None

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._RunInfinitely, daemon=True)
        self._thread.start()

    def Run(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self._loop)

    def Stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

    def _RunInfinitely(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

def GetLoop():
    if AsyncManager._instance is None:
        AsyncManager._instance = AsyncManager()
    return AsyncManager._instance