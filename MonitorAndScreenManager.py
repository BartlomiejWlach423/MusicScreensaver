import ctypes
from kivy.config import Config

def DetectAndSetupMonitor():
    fps=60

    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
    except Exception:
        width, height = 800, 800
    
    Config.set('graphics', 'width', width)    
    Config.set('graphics', 'height', height)
    Config.set('graphics', 'maxfps', fps)
    #Config.set('graphics', 'fullscreen', 'auto')
    print(f"Screen resolution: {width}, {height}")
