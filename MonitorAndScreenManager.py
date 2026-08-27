from screeninfo import get_monitors
from kivy.config import Config

def DetectAndSetupMonitor():
    fps=60

    monitors = get_monitors()
    primary = None

    if monitors:
        for monitor in monitors:
            if getattr(monitor, "is_primary", True):
                primary = monitor
        Config.set('graphics', 'width', primary.width)
        Config.set('graphics', 'height', primary.height)
    else:
        Config.set('graphics', 'width', 500)
        Config.set('graphics', 'height', 500)

    Config.set('graphics', 'maxfps', fps)
    #Config.set('graphics', 'fullscreen', 'auto')
    print(f"Screen resolution: {primary.width}, {primary.height}")
