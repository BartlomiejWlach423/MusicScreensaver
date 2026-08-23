import platform

OPERATING_SYSTEM = platform.system()

import kivy

class MusicScreensaver():
    def __init__(self):
        self.cover = None
        self.title = None
        self.artist = None

if __name__ == "__main__":
    if OPERATING_SYSTEM == "Windows":
        print("hello windows")
    else:
        print("Hello")