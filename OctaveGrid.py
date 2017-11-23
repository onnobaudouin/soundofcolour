import OpenCVHelpers as cvh
import math


class OctaveGrid:
    def __init__(self, width, height, padding=0, divisions_x=10, divisions_y=2, hysteresis=4):
        self.width = int(width)
        self.height = int(height)
        self.padding = int(padding)
        self.divisions_x = int(divisions_x)
        self.divisions_y = int(divisions_y)

        self.hysteresis = int(hysteresis)

        self.pwidth = self.width - (self.padding * 2)
        self.pheight = self.height - (self.padding * 2)

        self.xsize = math.floor(self.pwidth / self.divisions_x)
        self.ysize = math.floor(self.pheight / self.divisions_y)

        self.hit_width = self.xsize - (self.hysteresis * 2)
        self.hit_height = self.ysize - (self.hysteresis * 2)

        # print(str(self.height))

    def rect_for_hit(self, div_x, div_y):
        left = self.padding + (div_x * self.xsize) + self.hysteresis
        top = self.padding + (div_y * self.ysize) + self.hysteresis
        right = left + self.hit_width
        bottom = top + self.hit_height
        return left, top, right, bottom

    def pos_to_division(self, x, y):
        rx = x - self.padding
        ry = y - self.padding
        px = rx / self.pwidth
        py = ry / self.pheight
        ax = math.floor(px * self.divisions_x)
        ay = math.floor(py * self.divisions_y)

        # are we in hysteresis area?
        left, top, right, bottom = self.rect_for_hit(ax, ay)
        if (x < left) or (x > right):
            return ax, ay, False
        if (y < top) or (y > bottom):
            return ax, ay, False

        return ax, ay, True

    def draw_division_cell(self, frame, x, y, drawHit=False):
        xf = int(x * self.xsize) + self.padding
        yf = int(y * self.ysize) + self.padding
        cvh.draw_rect(frame, (xf, yf), (int(xf + self.xsize), int(yf + self.ysize)), (0, 200, 0), 1)
        if drawHit:
            left, top, right, bottom = self.rect_for_hit(x, y)
            # print(str(left)+' '+str(top)+' '+str(right)+' '+str(bottom))
            cvh.draw_rect(frame, (left, top), (right, bottom), (255, 255, 0), 1)

    def draw(self, frame):
        col = (128, 128, 128)

        for i in range(0, self.divisions_x + 1):
            x = int(i * self.xsize) + self.padding
            y1 = int(self.padding)
            y2 = int(self.height - self.padding)
            cvh.draw_line(frame, (x, y1), (x, y2), col)
        for i in range(0, self.divisions_y + 1):
            y = int(i * self.ysize) + self.padding
            x1 = int(self.padding)
            x2 = int(self.width - self.padding)
            cvh.draw_line(frame, (x1, y), (x2, y), col)
