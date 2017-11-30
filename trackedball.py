import math


class TrackedBall:
    next_id = 0

    def __init__(self, colour, pos, radius, area, contour=None):
        self.id = self.get_new_id()
        self.colour = colour
        self.pos = pos
        self.radius = radius
        self.area = area

        # self.velocity = None
        self.dead_frames = 0
        self.alive_frames = 0
        self.matched = False
        self.contour = contour
        # self.division = None

    @staticmethod
    def get_new_id():
        # todo compress id's?
        new_id = TrackedBall.next_id
        TrackedBall.next_id = TrackedBall.next_id + 1
        return new_id

    def update(self, ball):
        self.colour = ball.colour
        self.pos = ball.pos
        self.radius = ball.radius
        self.area = ball.area
        self.contour = ball.contour

    def area(self):
        return self.radius * self.radius * math.pi
