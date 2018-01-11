import hardware
from mouseinteraction import MouseInteraction
from framespersecond import FramesPerSecond
from threading import Thread
from videostream import VideoStream
from balltracker import BallTracker
from propertiesopencvui import *
from trackedball import TrackedBall
from trackedcolour import TrackedColour
from stateengine import *
import imageprocessing as imageprocessing
import traceback
import logging


class ColouredBallTracker(object):
    IS_RUNNING_ON_PI = hardware.is_raspberry_pi()

    def __init__(self):
        self.properties = self.create_properties()
        self.load_properties()
        self.properties_ui = PropertiesOpenCVUI(self.properties)
        self.video_stream = None
        self.video_resolution = None
        self.main_window_name = 'frame'

        # self.grid = None
        self.ball_tracker = BallTracker()
        self.mouse = MouseInteraction()
        self.main_loop_fps = FramesPerSecond()
        self.update_handler = None
        self.thread = None
        self.thread_should_be_running = False
        self.thread_killed_by_thread = False
        self.is_showing_ui = None

        self.frame = None
        self.last_frame = None
        self.sampling_frame = None
        self.sampling_frame_hsv = None
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

    def load_properties(self, filename: str = None):
        if filename is None:
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
        self.properties_ui.show('tracker')

    def close_properties(self):
        self.properties_ui.close()

    @classmethod
    def create_properties(cls) -> Properties:
        props = Properties('coloured_ball_tracker')
        tracker = props.add_group("tracker")
        tracker.add("blur", PropNodeType.unsigned_int, maximum=250)
        tracker.add("min_circle", PropNodeType.unsigned_int, maximum=250)
        tracker.add("max_circle", PropNodeType.unsigned_int, maximum=250)
        tracker.add("min_area", PropNodeType.unsigned_int, maximum=200)
        tracker.add("distance", PropNodeType.unsigned_float, minimum=0.0, maximum=1.0, default=0.05)

        ui = props.add_group("ui")
        ui.add("show_masks", PropNodeType.bool)

        colours2 = props.add_group("colours")
        cols = ["blue", "green", "yellow", "orange", "pink"]
        for name in cols:
            colour = colours2.add_group(name)
            colour.add('enabled', PropNodeType.bool, default=True)
            colour.add('rgb', PropNodeType.rgb)
            colour.add('min_hsv', PropNodeType.hsv)
            colour.add('max_hsv', PropNodeType.hsv)
        return props

    def change_resolution(self, resolution):
        print("updating to resolution: " + str(resolution))
        width, height = resolution
        # self.grid = OctaveGrid(width, height, padding=10, divisions_x=10, divisions_y=2)
        self.ball_tracker.set_max_distance(width * 0.05)
        pass

    def resolution(self):
        if self.frame is not None:
            return imageprocessing.resolution_of(self.frame)
        return -1, -1

    def coloured_balls_in(self, bgr_frame, colours, min_enclosing=0, max_enclosing=20,
                          min_area_in_pixels=10000000):
        # this is SLOW
        hsv_frame = imageprocessing.hue_saturation_value_frame_of(bgr_frame)
        self.sampling_frame_hsv = imageprocessing.clone_image(hsv_frame)

        new_balls = []

        for colour in colours:
            mask = imageprocessing.mask_of_colour(hsv_frame, colour.minimum_hsv, colour.maximum_hsv)

            # TODO: optimize for platform as usefull
            # # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel=morph_kernel(), iterations=1)
            # # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel=morph_kernel(), iterations=2)
            colour.mask = mask
            #
            contours = imageprocessing.contours_of_colour_range_in(colour.mask)

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
        colours_node = self.properties.node_at_path('colours')
        for colour_node in colours_node.child_nodes():
            if colour_node.value_of('enabled') is True:
                tracked_colour = TrackedColour(
                    name=colour_node.name,
                    minimum_hsv=imageprocessing.hsv_to_np_array(colour_node.value_of('min_hsv')),
                    maximum_hsv=imageprocessing.hsv_to_np_array(colour_node.value_of('max_hsv')),
                    rgb=colour_node.value_of('rgb')
                )
                tracked_colours.append(tracked_colour)
        return tracked_colours

    def process_frame(self, frame):
        active_colours = self.colours_to_track()

        props = self.properties

        # pre blur to smooth image
        blur = props.value_of('tracker/blur')
        if blur > 0:
            frame = imageprocessing.blur(frame, blur)

        min_enclosing = props.value_of('tracker/min_circle')
        max_enclosing = props.value_of('tracker/max_circle')
        min_area = props.value_of('tracker/min_area')
        max_distance = props.value_of('tracker/distance')

        width, height = imageprocessing.resolution_of(frame)

        self.ball_tracker.set_max_distance(width * max_distance)

        balls_in_frame, active_colours = self.coloured_balls_in(
            bgr_frame=frame,
            colours=active_colours,
            min_enclosing=min_enclosing,
            max_enclosing=max_enclosing,
            min_area_in_pixels=min_area * min_area)

        if self.is_showing_ui:
            show_masks = props.value_of('ui/show_masks')
            if show_masks is True:
                for colour in active_colours:
                    cv2.imshow('mask_' + colour.name, colour.mask)

        cv_draw_all = -1
        for ball in balls_in_frame:
            cv2.drawContours(frame, [ball.contour], cv_draw_all, imageprocessing.bgr_of(ball.colour.rgb))
            (x, y) = ball.pos
            cv2.circle(frame, (int(x), int(y)), int(ball.radius), imageprocessing.bgr_of(ball.colour.rgb), thickness=1)

        self.ball_tracker.update(balls_in_frame)

        for ball in self.ball_tracker.balls:
            x = int(ball.pos[0])
            y = int(ball.pos[1])
            imageprocessing.draw_text(frame, str(ball.id), (x, y))

        h = self.update_handler
        if h is not None:
            h()

        return frame

    def balls(self):
        return self.ball_tracker.balls

    def sample_colour(self, x, y, radius):
        hsv = imageprocessing.get_mean_hsv_from_circle_and_draw_debug(
            self.sampling_frame, (x, y), radius, self.frame)

        return hsv

    def sample_histogram(self, x, y, radius):
        return imageprocessing.histogram_of_disc(
            self.sampling_frame, (x, y), radius)

    def sample_histogram_hsv(self, x, y, radius):
        return imageprocessing.histogram_hsv_of_disc(
            self.sampling_frame_hsv, (x, y), radius)

    def update(self):
        """
        Attempts to fetch a new image from the video stream
        then does all the analyis as setup. So might not do anything if no new frame was available...
        :return:
        """
        vs = self.video_stream
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            self.frame = new_frame

            # if self.mouse.mode == MouseInteraction.DRAWING:
            self.sampling_frame = imageprocessing.clone_image(
                self.frame)  # moved into main as used a lot TODO: perf impact

            self.state.run()

            # mouse overlay
            if self.mouse.mode == MouseInteraction.DRAWING:
                self.mouse.draw_on(self.frame, self.sampling_frame)

            imageprocessing.draw_text(self.frame, "frame: " + str(frame_count) +
                                      ' fps:' + str(self.video_stream.frames_per_second.fps) +
                                      ' bounced: ' + str(self.video_stream.duplicate_frames_per_second_requests.fps) +
                                      ' loops/sec: ' + str(self.main_loop_fps.fps),
                                      pos=(10, int(imageprocessing.resolution_of(self.frame)[1] - 20)))

            if self.is_showing_ui:
                cv2.imshow(self.main_window_name, self.frame)

            self.last_frame = imageprocessing.clone_image(self.frame)

    def start(self):
        if self.is_thread_running():
            print("We are already running... ignored start request")
            return
        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread_should_be_running = True
        self.thread.start()

    def stop_and_wait_until_stopped(self):
        if self.is_thread_running() is False:
            print("Coloured Ball Tracker is already stopped - ignored")
            return
        # stop the thread and release any resources
        print("stopping coloured ball tracker")
        self.thread_should_be_running = False
        self.thread.join()  # this is blocking...
        self.thread = None
        print("stopped coloured ball tracker")

    def stop_thread_by_thread(self):
        """
        Call this to kill the thread from within it... this will lead to a cleaner cleanup
        """
        self.thread_killed_by_thread = True
        self.thread_should_be_running = False

    def is_thread_running(self):
        if self.thread_killed_by_thread is True:
            self.thread = None
            self.thread_killed_by_thread = False
        return self.thread is not None and self.thread.is_alive()

    def show_ui(self, state=True):
        if state == self.is_showing_ui:
            # print("same UI state, ignored")
            return
        self.is_showing_ui = bool(state)
        if self.is_showing_ui:
            print("showing UI")
            self.show_properties()
            cv2.namedWindow(self.main_window_name)  # for mouse events
            self.mouse.attach_to_window(self.main_window_name)

        else:
            self.close_properties()
            print("not showing UI")
            # what to do with MOUSe???

    def run(self):
        """
        Do not call directly use start instead.
        main loop to take care of all the processing

        this is a blocking call.

        Also deals with the UI, if any
        :return:
        """
        try:
            self.video_stream = self.start_video_stream()
            self.state.start('wait_for_first_frame')
            while self.thread_should_be_running:
                self.main_loop_fps.add()  # track only for performance reasons.
                self.show_ui(self.is_showing_ui)  # has the ui showing been changed?

                self.update()  # do a single frame update if possible.

                if self.is_showing_ui:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Pressed Quit")
                        self.stop_thread_by_thread()
                    if key == ord("s"):
                        self.state.start("stabilize")

        except Exception as ex:
            logging.error(traceback.format_exc())
        finally:
            self.show_ui(False)
            self.video_stream.stop_and_wait_until_stopped()

        if self.thread_killed_by_thread:
            print("Coloured Ball Thread is closing, as caused by Quit Action")

    def run_wait_for_first_frame(self):
        self.change_resolution(imageprocessing.resolution_of(self.frame))
        self.state.start("stabilize")

    def start_stabilize(self):
        print("start stabilizing image to allow white balance to be set by camera")
        self.video_stream.start_stabilize()

    def run_stabilize(self):
        if self.video_stream.is_stabilizing:
            imageprocessing.draw_text(self.frame, str(self.video_stream.stabilize_frame_counter) +
                                      ' stabilising', (5, 40), (255, 255, 255))
        else:
            self.state.start("normal")

    def run_normal(self):
        self.frame = self.process_frame(self.frame)

    def set_update_handler(self, handler):
        self.update_handler = handler


if __name__ == '__main__':
    col = ColouredBallTracker()
    col.show_ui(True)
    col.run()
