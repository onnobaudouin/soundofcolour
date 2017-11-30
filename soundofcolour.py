from hardware import *
from mouseinteraction import MouseInteraction
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
from trackedball import TrackedBall
from trackedcolour import TrackedColour
from stateengine import *


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
        self.ball_tracker = BallTracker()
        self.mouse = MouseInteraction()
        self.main_loop_fps = FramesPerSecond()

        self.frame = None
        self.state = StateEngine()
        self.state.add("wait_for_first_frame",
                       run=lambda x=self: x.run_wait_for_first_frame())
        self.state.add("stabilize",
                       start=lambda x=self: x.start_stabilize(),
                       run=lambda x=self: x.run_stabilize())
        self.state.add("normal",
                       run=lambda x=self: x.run_normal())

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
        self.properties_ui.show('colours/pink')
        self.properties_ui.show('colours/green')
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
        ui.add("min_area", PropType.unsigned_int, maximum=1920)

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
            mask = self.mask_of_colour(hsv_frame, colour.minimum_hsv, colour.maximum_hsv)

            # TODO: optimize for platform as usefull
            # # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel=morph_kernel(), iterations=1)
            # # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel=morph_kernel(), iterations=2)
            colour.mask = mask
            #
            contours = self.contours_of_colour_range_in(colour.mask)

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
                        ball = TrackedBall(
                            colour=colour,
                            radius=radius,
                            pos=(x, y),
                            area=area,
                            contour=contour
                        )
                        new_balls.append(ball)

        return new_balls, colours

    def colours_to_track(self):
        # todo: optimize with dirty versioning and return same as before
        # or dirty manual checking...
        tracked_colours = []
        colours_node = self.properties.node_from_path('colours')
        for (key, colour_node) in colours_node.groups.items():
            if colour_node.value_of('enabled') is True:
                tracked_colour = TrackedColour(
                    name=colour_node.name,
                    minimum_hsv=np.array(colour_node.value_of('min_hsv')),
                    maximum_hsv=np.array(colour_node.value_of('max_hsv')),
                    rgb=colour_node.value_of('rgb')
                )
                tracked_colours.append(tracked_colour)
        return tracked_colours

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
                cv2.imshow('mask_' + colour.name, colour.mask)
                #
        cv_draw_all = -1
        for ball in balls_in_frame:
            cv2.drawContours(frame, [ball.contour], cv_draw_all, self.bgr_of(ball.colour.rgb))
            (x, y) = ball.pos
            cv2.circle(frame, (int(x), int(y)), int(ball.radius), self.bgr_of(ball.colour.rgb), thickness=1)

        self.ball_tracker.update(balls_in_frame)

        for ball in self.ball_tracker.balls:
            x = int(ball.pos[0])
            y = int(ball.pos[1])
            cvh.draw_text(frame, str(ball.id), (x, y))

        return frame

    def bgr_of(self, rgb):
        (r, g, b) = rgb
        return (b, g, r)

    def update(self):
        vs = self.video_stream
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            self.frame = new_frame

            sampling_frame = None

            if self.mouse.mode == MouseInteraction.DRAWING:
                sampling_frame = cvh.clone_image(self.frame)

            self.state.run()

            # mouse overlay
            if self.mouse.mode == MouseInteraction.DRAWING:
                self.mouse.draw_on(self.frame, sampling_frame)

            cvh.draw_text(self.frame, "frame: " + str(frame_count) +
                          ' fps:' + str(self.video_stream.frames_per_second.fps) +
                          ' bounced: ' + str(self.video_stream.duplicate_frames_per_second_requests.fps) +
                          ' loops/sec: ' + str(self.main_loop_fps.fps), pos=(10, int(self.video_stream.resolution_of(self.frame)[1]-20)))

            cv2.imshow(self.main_window_name, self.frame)

    def run(self):
        self.show_properties()
        try:
            self.video_stream = self.start_video_stream()
            cv2.namedWindow(self.main_window_name)  # for mouse events
            self.mouse.attach_to_window(self.main_window_name)
            self.state.start('wait_for_first_frame')

            while True:
                self.main_loop_fps.add()
                self.update()
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                if key == ord("s"):
                    self.state.start("stabilize")

        except KeyboardInterrupt:
            print("CRTL + C")
        finally:
            self.close_properties()
            self.video_stream.start_stop()

    def run_wait_for_first_frame(self):
        self.change_resolution(self.video_stream.resolution_of(self.frame))
        self.state.start("stabilize")

    def start_stabilize(self):
        print("start stabilizing image to allow white balance to be set by camera")
        self.video_stream.start_stabilize()

    def run_stabilize(self):
        if self.video_stream.is_stabilizing:
            cvh.draw_text(self.frame, str(self.video_stream.stabilize_frame_counter) +
                          ' stabilising', (5, 40), (255, 255, 255))
        else:
            self.state.start("normal")

    def run_normal(self):
        self.frame = self.process_frame(self.frame)
        #cvh.draw_text(self.frame,
        #              # str(fps.fps) + 'fps ' +
        #              # str(ips.fps) + 'pips' +
        #              str(self.video_stream.frames_per_second.fps) + 'video fps', (5, 20), (255, 255, 255))


if __name__ == '__main__':
    soc = SoundOfColour()
    soc.run()
