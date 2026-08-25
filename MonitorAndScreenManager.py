from screeninfo import get_monitors
from kivy.config import Config

def DetectAndSetupMonitor():
    width_res = 500
    height_res = 500
    fps=60

    for monitor in get_monitors():
        width_res = max(monitor.width, width_res)
        height_res = max(monitor.height, height_res)

    Config.set('graphics', 'width', width_res)
    Config.set('graphics', 'height', height_res)
    Config.set('graphics', 'maxfps', fps)
    #Config.set('graphics', 'fullscreen', 'auto')
    print(f"Screen resolution: {width_res}, {height_res}")
