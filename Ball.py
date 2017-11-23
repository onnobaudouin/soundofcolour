import math


class Ball:
    next_id = 0

    def __init__(self, ball_tuple):
        self.id = self.get_new_id()

        colour, radius, pos, area = ball_tuple

        self.colour = colour
        self.pos = pos
        self.radius = radius
        self.area = area
        # self.velocity = None
        self.dead_frames = 0
        self.alive_frames = 0
        self.matched = False

        self.division = None

    @staticmethod
    def get_new_id():
        new_id = Ball.next_id
        Ball.next_id = Ball.next_id + 1
        return new_id

    def update(self, ball_tuple):
        colour, radius, pos, area = ball_tuple

        self.colour = colour
        self.pos = pos
        self.radius = radius
        self.area = area

    def area_of_circle(self):
        return self.radius * self.radius * math.pi
