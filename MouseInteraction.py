import cv2
import numpy as np

# mouse = []
# 'EVENT_FLAG_ALTKEY',
# 'EVENT_FLAG_CTRLKEY',
# 'EVENT_FLAG_LBUTTON',
# 'EVENT_FLAG_MBUTTON',
# 'EVENT_FLAG_RBUTTON',
# 'EVENT_FLAG_SHIFTKEY',
# 'EVENT_LBUTTONDBLCLK',
# 'EVENT_LBUTTONDOWN',
# 'EVENT_LBUTTONUP',
# 'EVENT_MBUTTONDBLCLK',
# 'EVENT_MBUTTONDOWN',
# 'EVENT_MBUTTONUP',
# 'EVENT_MOUSEHWHEEL',
# 'EVENT_MOUSEMOVE',
# 'EVENT_MOUSEWHEEL',
# 'EVENT_RBUTTONDBLCLK',
# 'EVENT_RBUTTONDOWN',
# 'EVENT_RBUTTONUP']


class MouseInteraction:
    DRAWING = 1

    def __init__(self):
        self.mode = None
        self.draw_pos = None
        self.draw_size = None
        self.draw_last_pos = None

    def handle_event(self, event, x, y, flags, param):
        if self.mode is None:
            if event == cv2.EVENT_RBUTTONDOWN:
                self.mode = MouseInteraction.DRAWING
                self.draw_pos = (x, y)
                self.draw_last_pos = (x, y)
                self.draw_size = 3
                return
        if self.mode == MouseInteraction.DRAWING:
            #  if event == cv2.EVENT_MOUSEWHEEL:
            #      offset = 0
            #     if flags > 0: #scroll up
            #          offset = 1
            #      elif flags < 0:
            #          offset = -1
            #      self.draw_size = self.draw_size + offset
            if event == cv2.EVENT_MOUSEMOVE:
                self.draw_last_pos = (x, y)
                dx = x - self.draw_pos[0]
                dy = y - self.draw_pos[1]

                dist = max(int(np.math.sqrt(dx * dx + dy * dy)), 1)
                # if dist <= 0:
                #    dist = 1
                self.draw_size = dist

            if event == cv2.EVENT_RBUTTONUP:
                self.mode = None
                self.draw_pos = None
                self.draw_size = 3


mouseInteraction = MouseInteraction()


def handler(event, x, y, flags, param):
    global mouseInteraction
    mouseInteraction.handle_event(event, x, y, flags, param)


def connect(window_name):
    cv2.setMouseCallback(window_name, handler)


def mouse():
    global mouseInteraction
    return mouseInteraction
