from ball import Ball
import sys


class BallTracker:
    def __init__(self, width):
        self.balls = []
        distance = width * 0.075
        self.max_distance_squared = distance * distance

    def update(self, new_balls):
        for ball in self.balls:
            ball.matched = False

        for new_ball in new_balls:
            best_match_ball = self.best_matching(new_ball)
            if best_match_ball is not None:
                best_match_ball.update(new_ball)
            else:
                best_match_ball = Ball(new_ball)
                self.balls.append(best_match_ball)

            best_match_ball.matched = True
            best_match_ball.alive_frames = best_match_ball.alive_frames + 1
            best_match_ball.dead_frames = 0

        for ball in self.balls:
            if not ball.matched:
                ball.dead_frames = ball.dead_frames + 1
                ball.alive_frames = 0

                # pprint(self.balls)
                # for b in self.balls:
                # print(str(b.id) + ' '+str(b.alive_frames))

        # weed out dead balls -
        self.balls = [i for i in self.balls if i.dead_frames < 5]

        ret = [i for i in self.balls if i.alive_frames > 1]

        # print (str(len(self.balls))+' '+str(len(ret)))

        return ret

    def best_matching(self, new_ball):
        if len(self.balls) == 0:
            return None

        comparisons = [self.compare(ball, new_ball) for ball in self.balls]
        ok = [i for i in comparisons if i is not None]
        if len(ok) > 0:
            ball, distance_squared, area = self.comparison_with_lowest_distance(ok)
            if distance_squared < self.max_distance_squared:
                return ball
        return None

    @staticmethod
    def comparison_with_lowest_distance(comparisons):
        min_distance = sys.maxsize
        min_object = None
        for c in comparisons:
            (o, distance_squared, area) = c
            if distance_squared < min_distance:
                min_distance = distance_squared
                min_object = c
        return min_object

    def compare(self, ball, new_ball):
        if ball.matched:
            return None
        colour, radius, pos, area = new_ball
        if ball.colour != colour:
            return None
        return (
            ball,
            self.distance_squared(ball.pos, pos),
            0
        )

    @staticmethod
    def distance_squared(pt1, pt2):
        dx = pt1[0] - pt2[0]
        dy = pt1[1] - pt2[1]
        return dx * dx + dy * dy
