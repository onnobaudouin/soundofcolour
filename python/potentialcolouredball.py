import math
from typing import List
import imageprocessing as imageprocessing


class PotentialColouredBall:
    circle = None
    color = None
    sub_circles = []
    probability = 0
    probabilities = None
    color_name = None
    hue = None
    range = None
    meaningfull_maxima = None
    blurred_hist = None
    greyness = None

    def __init__(self, circle):
        self.circle = circle



    def add_statistics(self, stats):
        probability, probabilities, color, hue, hue_range, meaningfull_maxima, blurred_hists, greyness = stats
        self.probability = probability
        self.probabilities = probabilities
        self.color_name = color
        self.hue = hue
        self.range = hue_range
        self.meaningfull_maxima = meaningfull_maxima
        self.blurred_hist = blurred_hists
        self.greyness = greyness

    def update_statistics(self, circle, hsv_frame, rgb_frame, draw_frame, debug=True):
        stats = PotentialColouredBall.statistics_of_circle_of_being_coloured_ball(circle,
                                                                                  hsv_frame,
                                                                                  rgb_frame,
                                                                                  draw_frame,
                                                                                  debug)
        self.add_statistics(stats)

    @staticmethod
    def coloured_balls(circles:List["PotentialColouredBall"], hsv_source, rgb_source, draw_frame, debug=False):
        circles = PotentialColouredBall.combined_clustered_circles(circles)

        for x in circles:
            x.update_statistics(x.circle, hsv_source, rgb_source, draw_frame, debug=debug)

        look_ok = [x for x in circles if x.probability > 0.90]

        circles = PotentialColouredBall.circles_with_minimal_overlap(look_ok)

        PotentialColouredBall.draw_many(draw_frame, circles, (255, 128, 128), 2)

    @staticmethod
    def combined_clustered_circles(
            circles: List["PotentialColouredBall"],
            center_distance=10) -> List["PotentialColouredBall"]:

        center_dist = center_distance ** 2
        clusters = []
        while len(circles) > 0:
            t = circles.pop()
            x1, y1, r1 = t.circle

            match = []
            no_match = []
            for other in circles:
                x2, y2, r2 = other.circle
                dx = x2 - x1
                dy = y2 - y1
                dist = dx ** 2 + dy ** 2
                if dist < center_dist:
                    match.append(other)
                else:
                    no_match.append(other)

            t.sub_circles = match
            clusters.append(t)
            circles = no_match

        for f in clusters:
            x, y, r = f.circle
            for sub_circle in f.sub_circles:
                x2, y2, r2 = sub_circle.circle
                x = x + x2
                y = y + y2
                r = r + r2
            parts = 1 + len(f.sub_circles)
            f.circle = (int(x / parts), int(y / parts), int(r / parts))

        return clusters

    @staticmethod
    def circles_with_minimal_overlap(
            circles: List["PotentialColouredBall"],
            tolerance_in_radius_overlap=1) -> List["PotentialColouredBall"]:
        """remove any circles that have overlap"""
        bad_indexes = []
        for index1, circle1 in enumerate(circles):
            x1, y1, r1 = circle1.circle
            for index2, circle2 in enumerate(circles):
                if index1 != index2:
                    x2, y2, r2 = circle2.circle
                    dx = x2 - x1
                    dy = y2 - y1
                    dist = math.sqrt(dx * dx + dy * dy)
                    radii = r1 + r2
                    if dist < radii:
                        overlap = radii - dist
                        if overlap > tolerance_in_radius_overlap:
                            bad_indexes.append(index1)
                            bad_indexes.append(index2)

        return [circle for index, circle in enumerate(circles) if index not in bad_indexes]

    @staticmethod
    def statistics_of_circle_of_being_coloured_ball(circle, hsv_frame, rgb_frame, draw_frame, debug=True):
        x, y, r = circle

        # we reduce the radius a tiny bit so we don't pick up on too much noise at the edges...
        radius_adjust = 3
        r = r - radius_adjust
        if r < 3:
            # pointless to look
            return 0

        probabilities = []

        if debug:
            imageprocessing.draw_circle(draw_frame, (x, y), r, (255, 255, 20))

        (mean, stddev) = imageprocessing.mean_and_stddev_of_disc(rgb_frame, (x, y), r)
        hsv = imageprocessing.bgr_to_hsv(mean[0], mean[1], mean[2])
        p = [int(x) for x in stddev]
        for index, value in enumerate(p):
            if (value / 255.0) > 0.20:
                probabilities.append((0.5, 'std dev rgb too high ' + str(index)))

        if hsv[1] / 255.0 < 0.10:
            probabilities.append((0.3, 'too low sat'))

        # we check if the average colour is just to 'grey'
        min_value = 256
        max_value = 0
        for col in mean:
            min_value = min(min_value, col)
            max_value = max(max_value, col)
        greyness = (max_value - min_value) / 255.0
        if greyness < 0.1:  # the range between each channel is just 10 percent...
            probabilities.append((0.5, 'too grey'))

        outside_radius = 10

        # now we check the area AROUND the circle and see what that average colour is...
        (mean2, stddev2) = imageprocessing.mean_and_stddev_of_torus(rgb_frame, (x, y),
                                                                    r + radius_adjust,
                                                                    r + radius_adjust + outside_radius)

        distance = imageprocessing.distance_between_rgb_colours(mean, mean2)
        if distance < 0.15:
            probabilities.append((0.80, 'area around is too similar'))

        # hue_difference = abs(self.minimum_angle_between_2_angles(hsv[0], hsv2[0], radians=False)) / 360.0f
        # sat_difference = abs(hsv[1]-hsv2[1]) / 255.0
        # lum_difference = abs(hsv[2] - hsv2[2]) / 255.0
        #
        # if (hue_difference + sat_difference + lum_difference) < 0.10:
        #     probabilities.append((0.3, 'outside too similar to inside'))

        if debug:
            # imageprocessing.draw_circle(draw_frame, (x, y), r + radius_adjust, (0, 0, 255))
            # imageprocessing.draw_circle(draw_frame, (x, y), r + radius_adjust + outside_radius, (0, 0, 255))
            # imageprocessing.draw_disc(draw_frame, (x - (r + radius_adjust) - (outside_radius // 2), y),
            #                          outside_radius // 2, mean2)

            imageprocessing.draw_text(draw_frame, str(int(distance * 100)), (x - 75, y))

        hists_hsv = imageprocessing.histogram_hsv_of_disc(hsv_frame, (x, y), r)

        signal_cutoff = 0.0075
        # smooth the histograms
        blurred_hists = []

        hue = None
        meaningfull_maxima = None

        for index, histogram in enumerate(hists_hsv):
            blurred_hist = imageprocessing.blur_histogram(histogram, 5, circular=(index == 0), times=9)
            normalized_hist = imageprocessing.normalize_histogram(blurred_hist)
            normalized_hist = imageprocessing.low_filter_histogram(normalized_hist, signal_cutoff)  # kill low epsilons
            blurred_hists.append(normalized_hist)

            if index == 0:  # hue
                local_maxima = imageprocessing.local_maxima_indices_in_histogram_1d(normalized_hist,
                                                                                    circular=(index == 0))
                meaningfull_maxima = [x for x in local_maxima if normalized_hist[x] > 0.25]
                if len(meaningfull_maxima) > 1:
                    probabilities.append((0.05, "multiple HUE maxima"))
                else:
                    hue = meaningfull_maxima[0] * 2  # * 2 as we only have 0->179 Hue values, map to 360
                # return 0 # the HUE histogram has more then 1 significant bump...
            # else:
            # hue chec ok...
            # probabilities.append((1, ""))
            # spread = imageprocessing.spread_min_max(normalized_hist, threshold=0.05, percentage=True)

            if index == 1:  # stauration
                min_max = imageprocessing.min_max_indices_if_over_strength(normalized_hist, threshold=0.05,
                                                                           percentage=True)
                if min_max is not None:
                    min_index, max_index = min_max
                    if max_index < 0.20:
                        probabilities.append((0.05, "very low saturation max"))

            if index == 2:  # luminosity
                min_max = imageprocessing.min_max_indices_if_over_strength(normalized_hist, threshold=0.05,
                                                                           percentage=True)
                if min_max is not None:
                    min_index, max_index = min_max
                    if max_index < 0.10:
                        probabilities.append((0.05, "very low luminosity max"))

        # colour_differences_percentages = self.colour_distance_signal(rgb_frame, (x,y,r), extra_range=8, sample_radius_size=1)
        # coldif = imageprocessing.gaussian_blur_1d(colour_differences_percentages,size=7,circular=False)
        # imageprocessing.draw_line(draw_frame, (x + r, y), (x + r, y - 50), colour=(0, 255, 0))
        # imageprocessing.draw_histogram(draw_frame, (x , y), coldif, scale=50, normalize=True, colour=(128,255,255))

        expected = [
            (120, 160, "green", 10),
            (316, 350, "pink", 8),
            (208, 225, "blue", 8),
            (55, 75, "yellow", 8)]

        color = None
        range = None
        if hue is not None:
            for min_hue, max_hue, name, r in expected:
                if min_hue <= hue <= max_hue:
                    color = name
                    range = r
                    break

        probability = 1.0
        reasons = []
        for p in probabilities:
            probability = probability * p[0]
            reasons.append(p[1])

        if debug:
            imageprocessing.draw_histograms(x, y, blurred_hists, draw_frame)
            imageprocessing.draw_text(draw_frame, str(int(probability * 100)) + '% '.join(reasons), (x, y - 10))
            imageprocessing.draw_text(draw_frame, str(color) + ' ' + str(hue), (x - 30, y - 30))

        return probability, probabilities, color, hue, range, meaningfull_maxima, blurred_hists, greyness

    def draw_many(draw_frame, circles:List["PotentialColouredBall"], color=(255,128,128), thickness=1):
        for circle in circles:
            x, y, r = circle.circle
            imageprocessing.draw_circle(draw_frame, (x, y), r, color, thickness)