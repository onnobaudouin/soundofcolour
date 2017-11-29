from hardware import *
import MouseInteraction as mouse
from Colour import Colour
import opencvhelpers as cvh
from framespersecond import FramesPerSecond

from videostream import VideoStream
from balltracker import BallTracker
from OctaveGrid import OctaveGrid
from soundsocketserver import SoundSocketServer
from simplewebserver import *
from web import *
from propertiesopencvui import *
import numpy as np
from transitions import Machine  # https://github.com/pytransitions/transitions
from collections import namedtuple
from ball import Ball


class SoundOfColour(object):
    IS_RUNNING_ON_PI = is_raspberry_pi()

    def __init__(self):
        self.properties = self.create_properties()
        self.load_properties()
        self.properties_ui = PropertiesOpenCVUI(self.properties)
        self.video_stream = None
        self.video_resolution = None
        self.main_window_name = 'frame'
        self.has_received_first_valid_frame = False
        self.grid = None
        self.state = None
        self.ball_tracker = BallTracker()

    def change_state_to(self, new_state):
        print("change state from " + str(self.state) + " -> " + str(new_state))
        self.state = new_state

    def start_video_stream(self) -> VideoStream:
        recommended_video_resolution, recommended_frame_rate = self.recommended_video_resolution_and_frame_rate()
        vs = VideoStream.create(wanted_frame_rate=recommended_frame_rate,
                                wanted_resolution=recommended_video_resolution,
                                use_pi_camera=self.IS_RUNNING_ON_PI)

        if self.IS_RUNNING_ON_PI:
            vs.flip_horizontal(True)

        vs.start()

        return vs

    # based on runtime situation select appropriate
    def recommended_video_resolution_and_frame_rate(self):
        if self.IS_RUNNING_ON_PI:
            multiplier = 100  # 120 is fine for 30fps, 2 colours
            resolution = (4 * multiplier, 3 * multiplier + 4)
            frame_rate = 30
        else:
            resolution = (int(1280 / 2), int(720 / 2))
            frame_rate = 60
        return resolution, frame_rate

    def load_properties(self):
        if self.IS_RUNNING_ON_PI:
            filename = "pi.json"
        else:
            filename = "onno.json"
        self.properties.load(filename)

    def show_properties(self):
        self.properties_ui.show('colours/blue')
        self.properties_ui.show('ui')

    def close_properties(self):
        self.properties_ui.close()

    def create_properties(self) -> Properties:
        props = Properties()
        ui = props.group("ui")
        ui.add("blur", PropType.unsigned_int, maximum=250)
        ui.add("min_circle", PropType.unsigned_int, maximum=250)
        ui.add("max_circle", PropType.unsigned_int, maximum=250)
        ui.add("show_masks", PropType.bool)
        ui.add("min_area", PropType.unsigned_int)

        colours2 = props.group("colours")
        col = ["blue", "green", "yellow", "orange", "pink"]
        for name in col:
            colour = colours2.group(name)
            colour.add('enabled', PropType.bool, default=True)
            colour.add('rgb', PropType.rgb)
            colour.add('min_hsv', PropType.hsv)
            colour.add('max_hsv', PropType.hsv)
        return props

    def change_resolution(self, resolution):
        print("updating to resolution: " + str(resolution))
        width, height = resolution
        self.grid = OctaveGrid(width, height, padding=10, divisions_x=10, divisions_y=2)
        self.ball_tracker.set_max_distance(width * 0.05)
        pass

    def blur(self, frame, size):
        # todo: change dependant on platform?
        # frame = cv2.bilateralFilter(frame, 9, 75, 75)  # might be better
        # frame = cv2.medianBlur(frame, 15)
        if size % 2 == 0:
            size = size + 1
        return cv2.GaussianBlur(frame, (size, size), 0)

    def show_difference(self, original_frame, new_frame):
        if original_frame is not None:
            diff = cv2.absdiff(original_frame, new_frame)
            cv2.imshow('diff', diff)

    def mask_of_colour(self, input_frame_hsv, lower_range, higher_range):
        return cv2.inRange(input_frame_hsv, lower_range, higher_range)

    def contours_of_colour_range_in(self, mask_frame):

        # http://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
        # we use external so any small 'gaps' are ignored, e.g. a highlight for example within a sphere..
        image, contours, hierarchy = cv2.findContours(mask_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        return contours

    def hue_saturation_value_frame_of(self, bgr_frame):
        return cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)

    def coloured_balls_in(self, bgr_frame, colours, min_enclosing=0, max_enclosing=20,
                          min_area_in_pixels=10000000):
        # this is SLOW
        hsv_frame = self.hue_saturation_value_frame_of(bgr_frame)

        new_balls = []

        for colour in colours:
            mask = self.mask_of_colour(hsv_frame, colour['min'], colour['max'])

            # # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel=morph_kernel(), iterations=1)
            # # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel=morph_kernel(), iterations=2)
            colour['mask'] = mask
            #
            contours = self.contours_of_colour_range_in(colour['mask'])

            for contour in contours:
                # todo profile which is the quickest bounce
                (x, y), radius = cv2.minEnclosingCircle(contour)

                if min_enclosing < radius < max_enclosing:
                    area = cv2.contourArea(contour)
                    if area > min_area_in_pixels:
                        # cv2.circle(frame, (int(x), int(y)), 4, (255, 255, 0), thickness=cv2.FILLED)
                        # moments = cv2.moments(contour)
                        # m00 = moments["m00"]
                        # if m00 != 0:
                        #   center = (int(moments["m10"] / m00), int(moments["m01"] / m00))
                        #  cv2.circle(img=frame, center=center, radius=3, color=(0, 0, 255), thickness=cv2.FILLED)
                        ball = Ball(
                            colour=colour,
                            radius=radius,
                            pos=(x, y),
                            area=area,
                            contour=contour
                        )
                        new_balls.append(ball)

        return new_balls, colours

    def colours_to_track(self):
        # todo: optimize
        colour_infos = []
        colours_node = self.properties.node_from_path('colours')
        for (key, colour_node) in colours_node.groups.items():
            if colour_node.value_of('enabled') is True:
                colour_info = dict(
                    mask=None,
                    name=colour_node.name,
                    min=np.array(colour_node.value_of('min_hsv')),
                    max=np.array(colour_node.value_of('max_hsv')),
                    rgb=colour_node.value_of('rgb')
                )
                colour_infos.append(colour_info)
        return colour_infos

    def process_frame(self, frame):
        active_colours = self.colours_to_track()

        # pre blur to smooth image
        blur = self.properties.value_of('ui/blur')
        if blur > 0:
            frame = self.blur(frame, blur)

        min_enclosing = self.properties.value_of('ui/min_circle')
        max_enclosing = self.properties.value_of('ui/max_circle')
        min_area = self.properties.value_of('ui/min_area')

        balls_in_frame, active_colours = self.coloured_balls_in(
            bgr_frame=frame,
            colours=active_colours,
            min_enclosing=min_enclosing,
            max_enclosing=max_enclosing,
            min_area_in_pixels=min_area * min_area)

        show_masks = self.properties.value_of('ui/show_masks')
        if show_masks is True:
            for colour in active_colours:
                cv2.imshow('mask_' + colour['name'], colour['mask'])
#
        DRAW_ALL = -1
        for ball in balls_in_frame:
            cv2.drawContours(frame, [ball.contour], DRAW_ALL, self.bgr_of(ball.colour['rgb']))
            (x, y) = ball.pos
            cv2.circle(frame, (int(x), int(y)), int(ball.radius),  self.bgr_of(ball.colour['rgb']), thickness=1)

        self.ball_tracker.update(balls_in_frame)

        return frame

    def bgr_of(self, rgb):
        (r, g, b) = rgb
        return (b, g, r)


    def update(self):
        vs = self.video_stream
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            # on resolution confirmation / change
            if not self.has_received_first_valid_frame:
                self.change_resolution(resolution)
                self.has_received_first_valid_frame = True

            # original = cvh.clone_image(new_frame) # only needed when masking colours!

            if self.state == 'stabilize':
                if vs.is_stabilizing:
                    cvh.draw_text(new_frame, str(vs.stabilize_frame_counter) +
                                  ' stabilising', (5, 40), (255, 255, 255))
                else:
                    self.change_state_to('normal')

            if self.state == 'normal':
                new_frame = self.process_frame(new_frame)

                cvh.draw_text(new_frame,
                         # str(fps.fps) + 'fps ' +
                         # str(ips.fps) + 'pips' +
                          str(vs.frames_per_second.fps) + 'video fps', (5, 20), (255, 255, 255))

            # print("frame: " + str(frame_count) +
            #       ' fps:' + str(self.video_stream.frames_per_second.fps) +
            #       'bounced: ' + str(self.video_stream.duplicate_frames_per_second_requests.fps))
            cv2.imshow(self.main_window_name, new_frame)

    def run(self):
        self.show_properties()
        try:
            self.video_stream = self.start_video_stream()
            cv2.namedWindow(self.main_window_name)  # for mouse events
            self.change_state_to('stabilize')  # todo: wrap in state machine
            self.video_stream.start_stabilize()
            while True:
                self.update()
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
        except KeyboardInterrupt:
            print("CRTL+C")
        finally:
            self.close_properties()
            self.video_stream.start_stop()


if __name__ == '__main__':
    soc = SoundOfColour()
    soc.run()
