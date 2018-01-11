import cv2
import numpy as np
import imageprocessing as imageprocessing

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
    NONE = None

    def __init__(self):
        self.mode = None
        self.original_pos = None
        self.radius = None
        self.pos = None

    def handle_event(self, event, x, y, flags=None, param=None):
        self.pos = (x, y)
        if self.mode == MouseInteraction.NONE:
            if event == cv2.EVENT_RBUTTONDOWN:
                self.mode = MouseInteraction.DRAWING
                self.original_pos = (x, y)

                self.radius = 3
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
                dx = x - self.original_pos[0]
                dy = y - self.original_pos[1]
                dist = max(int(np.math.sqrt(dx * dx + dy * dy)), 1)
                # if dist <= 0:
                #    dist = 1
                self.radius = dist

            if event == cv2.EVENT_RBUTTONUP:
                self.mode = MouseInteraction.NONE
                self.original_pos = None
                self.radius = 3

    def attach_to_window(self, window_name):
        cv2.setMouseCallback(window_name,
                             lambda event, x, y, flags, param: self.handle_event(event, x, y, flags, param))

    def draw_on(self, frame, sampling_frame):
        if frame is None:
            print("Warning, printing on framw with None, ignored")
            return
        if sampling_frame is None:
            print("Warning, printing on sampling frame with None, ignored")
            return

        (mean, stddev) = imageprocessing.mean_and_stddev_of_circle(sampling_frame, self.original_pos, self.radius)
        hsv = imageprocessing.bgr_to_hsv(mean[0], mean[1], mean[2])

        cv2.circle(frame, self.original_pos, self.radius, (255, 0, 0), 1)
        imageprocessing.draw_shadow_arrow(frame, self.original_pos, self.pos)
        imageprocessing.draw_disc(frame, self.original_pos, radius=5, colour=mean)
        p = [int(x) for x in stddev]
        imageprocessing.draw_text(frame, str(hsv) + ' ' + str(p), self.pos)

