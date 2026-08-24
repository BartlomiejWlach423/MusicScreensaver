from screeninfo import get_monitors

def DetectAndSetupMonitor():
    monitors = []

    for monitor in get_monitors():
        monitors.append(monitor)

    monitors_len = len(monitors)

    max_width_res = 500
    height_res = 500

    if monitors_len>1:
        max_width_res = monitors[0].width
        height_res = monitors[0].height
        for monitor in monitors:
            if monitor.width > max_width_res:
                max_width_res = monitor.width
                height_res = monitor.height

    SetGraphicsParameters(width=max_width_res, height=height_res)
    print(f"Screen resolution: {max_width_res}, {height_res}")

from kivy.config import Config

def SetGraphicsParameters(width=500, height=500, fps='60', fullstreen='auto'):
    Config.set('graphics', 'width', width)
    Config.set('graphics', 'height', height)
    Config.set('graphics', 'maxfps', fps)
    #Config.set('graphics', 'fullscreen', 'auto')
    #Config.getint('kivy', 'show_fps')