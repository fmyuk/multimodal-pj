import mss
import numpy as np
from PIL import Image

class ScreenCapturer:
    def __init__(self, mode='full', region=None, fps=2):
        self.mode = mode
        self.region = region  # (left, top, width, height)
        self.fps = fps
        self.sct = mss.mss()
        self.running = False

    def start(self, callback):
        import threading, time
        self.running = True
        def loop():
            while self.running:
                img = self.capture()
                if img is not None:
                    callback(img)
                time.sleep(1.0 / self.fps)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False

    def capture(self):
        if self.mode == 'full':
            monitor = self.sct.monitors[1]
        elif self.mode == 'region' and self.region:
            monitor = {
                'left': self.region[0],
                'top': self.region[1],
                'width': self.region[2],
                'height': self.region[3],
            }
        else:
            monitor = self.sct.monitors[1]
        img = self.sct.grab(monitor)
        return Image.frombytes('RGB', img.size, img.rgb)
