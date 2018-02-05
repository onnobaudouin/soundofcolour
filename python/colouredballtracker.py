import hardware
from mouseinteraction import MouseInteraction
from framespersecond import FramesPerSecond
import threading
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
import numpy as np
import queue
from typing import Tuple, List, Any
from potentialcolouredball import PotentialColouredBall


class ColouredBallTracker(object):
    IS_RUNNING_ON_PI = hardware.is_raspberry_pi()

    def __init__(self):
        self.properties = self.create_properties()
        self.load_properties()
        self.properties_ui = PropertiesOpenCVUI(self.properties)
        self.video_stream = None
        self.video_resolution = None
        self.main_window_name = 'frame'

        self.busy = False

        # self.grid = None
        self.ball_tracker = BallTracker()
        self.mouse = MouseInteraction()
        self.main_loop_fps = FramesPerSecond()
        self.update_handler = None
        self.frame_handler = None
        self.thread = None
        self.thread_should_be_running = False

        self.is_showing_ui = False
        self.should_be_showing_ui = False

        self.frame = None
        self.sampling_frame = None
        self.sampling_frame_hsv = None

        self.average_background_frame = None
        self.average_background_accumulator = None
        self.average_background_count = None

        self.background_frame = None
        self.difference_mask = None

        self.gaussian_blur_frame = None
        self.hue_frame = None
        #self.hue_as_bgr_frame = None
        self.sat_frame = None
        self.lum_frame = None
        #self.limited_mask = None
        #self.canny = None

        self.last_colours = None

        self.state = StateEngine()
        self.state.add("wait_for_first_frame",
                       run=lambda x=self: x.run_wait_for_first_frame())
        self.state.add("stabilize",
                       start=lambda x=self: x.start_stabilize(),
                       run=lambda x=self: x.run_stabilize())
        self.state.add("normal",
                       run=lambda x=self: x.run_normal())
        self.state.add("average_background",
                       start=lambda x=self: x.start_average_background(),
                       run=lambda x=self: x.run_average_background())
        self.state.add("calibrate",
                       start=lambda x=self: x.start_calibrate(),
                       run=None)
        #  self.state.add("find_blobs",
        # #              start=lambda x=self: x.start_find_blobs(),
        #               run=None)

        self.internal_message_queue = queue.Queue()
        self.main_thread_q = queue.Queue()

    def start_video_stream(self) -> VideoStream:
        recommended_video_resolution, recommended_frame_rate = self.recommended_video_resolution_and_frame_rate()
        vs = VideoStream.create(wanted_frame_rate=recommended_frame_rate,
                                wanted_resolution=recommended_video_resolution,
                                use_pi_camera=self.IS_RUNNING_ON_PI)

        if self.IS_RUNNING_ON_PI:
            vs.flip_horizontal(True)

        vs.on_frame(self.on_video_stream_frame_handler)
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
                filename = "../pi.json"
            else:
                filename = "../onno.json"
        self.properties.load(filename)

    def show_properties(self):
        self.properties_ui.show('colours/blue')
        self.properties_ui.show('colours/pink')
        self.properties_ui.show('colours/green')
        self.properties_ui.show('ui')
        self.properties_ui.show('tracker')
        self.properties_ui.show('hough')

    def close_properties(self):
        self.properties_ui.close()

    @classmethod
    def create_properties(cls) -> Properties:
        props = Properties('coloured_ball_tracker')
        h = props.add_group("hough")
        h.add("min_dist", PropNodeType.unsigned_int, minimum=1, maximum=250, default=20)
        h.add("min_radius", PropNodeType.unsigned_int, minimum=1, maximum=250, default=5)
        h.add("max_radius", PropNodeType.unsigned_int, minimum=1, maximum=250, default=100)
        h.add("p1", PropNodeType.unsigned_int, minimum=1, maximum=250, default=50)
        h.add("p2", PropNodeType.unsigned_int, minimum=1, maximum=250, default=30)
        h.add("acc", PropNodeType.unsigned_float, minimum=0.1, maximum=10.0, default=1.5)

        tracker = props.add_group("tracker")
        tracker.add("blur", PropNodeType.unsigned_int, maximum=250)
        tracker.add("min_circle", PropNodeType.unsigned_int, maximum=250)
        tracker.add("max_circle", PropNodeType.unsigned_int, maximum=250)
        tracker.add("min_area", PropNodeType.unsigned_int, maximum=200)
        tracker.add("distance", PropNodeType.unsigned_float, minimum=0.0, maximum=1.0, default=0.05)
        tracker.add("averaged_frames", PropNodeType.unsigned_int, minimum=1, maximum=250, default=30)
        tracker.add("median", PropNodeType.unsigned_int, minimum=1, maximum=250, default=17)
        tracker.add("debug", PropNodeType.bool, default=False)

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
                          min_area_in_pixels=10000000) -> Tuple[List[TrackedBall], Any]:
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
                tracked_colour.min_values = colour_node.value_of('min_hsv')
                tracked_colour.max_values = colour_node.value_of('max_hsv')
                tracked_colours.append(tracked_colour)
        return tracked_colours

    def find_and_track_coloured_balls_in_frame(self, frame):
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

        index = 0
        for colour in active_colours:
            imageprocessing.draw_text(frame, str(colour.name), (10, index * 20 + 15))
            imageprocessing.draw_text(frame, 'min: ' + str(colour.minimum_hsv), (20, (index + 1) * 20 + 15))
            imageprocessing.draw_text(frame, 'max: ' + str(colour.maximum_hsv), (20, (index + 2) * 20 + 15))
            index = index + 3

        balls_in_frame, active_colours = self.coloured_balls_in(
            bgr_frame=frame,
            colours=active_colours,
            min_enclosing=min_enclosing,
            max_enclosing=max_enclosing,
            min_area_in_pixels=min_area * min_area)

        self.last_colours = active_colours

        # visual feedback only...
        cv_draw_all = -1
        for ball in balls_in_frame:
            cv2.drawContours(frame, [ball.contour], cv_draw_all, imageprocessing.bgr_of(ball.colour.rgb))
            (x, y) = ball.pos
            cv2.circle(frame, (int(x), int(y)), int(ball.radius), imageprocessing.bgr_of(ball.colour.rgb), thickness=1)

        self.ball_tracker.update(balls_in_frame)

        # visual feedback
        for ball in self.ball_tracker.balls:
            x = int(ball.pos[0])
            y = int(ball.pos[1])
            imageprocessing.draw_text(frame, str(ball.id), (x, y))

        h = self.update_handler
        if h is not None:
            h()

        return frame



    def set_background_to_average_background(self):
        if self.average_background_frame is None:
            print("We have no valid average background at the moment, ignored request")
            return
        self.background_frame = self.average_background_frame

    def find_potential_coloured_balls(self,
                                      channels,
                                      draw_frame,
                                      debug=False) -> List[PotentialColouredBall]:
        balls = []
        for index, frame in enumerate(channels):
            circles = self.hough_circles(frame)
            if circles is not None:
                circle_tuples = np.round(circles[0, :]).astype("int")
                for x in circle_tuples:
                    balls.append(PotentialColouredBall(x))
                # debug visualisation
                # if debug:
                #   imageprocessing.draw_circles(self.gaussian_blur_frame, draw_frame)
        return balls

    def find_coloured_balls(self, image):
        debug = self.properties.value_of('tracker/debug')
        # blur by gaussian
        self.gaussian_blur_frame = imageprocessing.blur(
            image,
            self.prop_value('tracker/median'))
        blurred_hsv = imageprocessing.hue_saturation_value_frame_of(self.gaussian_blur_frame)

        # we all use all 6 channels to detect circles...
        self.hue_frame, self.sat_frame, self.lum_frame = cv2.split(blurred_hsv)

        channels = [self.hue_frame, self.sat_frame, self.lum_frame] + cv2.split(self.gaussian_blur_frame)

        circles = self.find_potential_coloured_balls(channels, blurred_hsv, debug)

        balls = PotentialColouredBall.coloured_balls(circles, blurred_hsv, image, self.gaussian_blur_frame, debug)

        return balls

    def calibrate_fast_colour_tracked_from_coloured_balls(self, balls: List[PotentialColouredBall]):
        # now we calibrate
        # we should add all 'greens' etc but that's later..
        # todo: merge histograms for all same colours
        # check if all circles are in same size, i.e. cluster by size, remove outliers.
        for circle in balls:
            if circle.color_name is not None:
                pre = 'colours/' + circle.color_name + '/'
                min_hsv = (circle.hue - circle.range, 100 / 255.0, 50 / 255.0)
                max_hsv = (circle.hue + circle.range, 255 / 255.0, 255 / 255.0)

                # then train the image to see if it find the same using simple algo and complicated one..
                self.properties.set_value_of(pre + 'min_hsv', min_hsv)
                self.properties.set_value_of(pre + 'max_hsv', max_hsv)

    def hough_circles(self, frame):
        return cv2.HoughCircles(frame,
                                cv2.HOUGH_GRADIENT,
                                self.prop_value('hough/acc'),
                                self.prop_value('hough/min_dist'),
                                param1=self.prop_value('hough/p1'),
                                param2=self.prop_value('hough/p2'),
                                minRadius=self.prop_value('hough/min_radius'),
                                maxRadius=self.prop_value('hough/max_radius'))

    def on_video_stream_frame_handler(self):
        # print("Image received on thread: " + str(threading.current_thread().ident))
        if self.busy is False:
            self.busy = True
            self.update()
            self.internal_message_queue.put("image")
            self.busy = False
        else:
            print("Not enough performance...")

    def update(self):
        """
        Attempts to fetch a new image from the video stream
        then does all the analysis as setup. So might not do anything if no new frame was available...
        :return:
        """
        vs = self.video_stream
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            self.frame = new_frame

            # if self.background_frame is not None:
            #     difference_mask = cv2.absdiff(self.frame, self.background_frame)
            #     img2gray = cv2.cvtColor(difference_mask, cv2.COLOR_BGR2GRAY)
            #     ret, self.difference_mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)

            # if self.mouse.mode == MouseInteraction.DRAWING:
            self.sampling_frame = imageprocessing.clone_image(
                self.frame)  # moved into main as used a lot TODO: perf impact

            self.state.run()

            # mouse overlay
            if self.mouse.mode == MouseInteraction.DRAWING or self.mouse.mode == MouseInteraction.STATIC:
                self.mouse.draw_on(self.frame, self.sampling_frame)
                if self.sampling_frame_hsv is not None:
                    if self.mouse.original_pos is not None:
                        x, y = self.mouse.original_pos
                        PotentialColouredBall.statistics_of_circle_of_being_coloured_ball(
                            (x, y, self.mouse.radius),
                            self.sampling_frame_hsv,
                            self.sampling_frame,
                            self.frame
                        )

            imageprocessing.draw_text(self.frame, "frame: " + str(frame_count) +
                                      ' fps:' + str(self.video_stream.frames_per_second.fps),
                                      pos=(10, int(imageprocessing.resolution_of(self.frame)[1] - 20)))

            # self.last_frame = imageprocessing.clone_image(self.frame)  # this can be removed...

            self.fire_frame_handler(frame_count)

    def start(self):
        if self.is_thread_running():
            print("We are already running... ignored start request")
            return
        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread_should_be_running = True
        self.thread.start()
        print("Coloured Ball Main Loop Thread: " + str(self.thread.ident))

    def stop(self):
        self.video_stream.stop_and_wait_until_stopped()
        self.thread_should_be_running = False

    def stop_and_wait_until_stopped(self):

        # stop the thread and release any resources
        print("stopping coloured ball tracker")
        self.stop()
        self.wait_until_stopped()

    def wait_until_stopped(self):
        self.thread.join()
        print("Closed Coloured Ball Main Loop Thread: " + str(self.thread.ident))
        self.thread = None

    def is_thread_running(self):
        return self.thread is not None and self.thread.is_alive()

    def update_ui(self, caller=None):

        if self.is_showing_ui and not self.should_be_showing_ui:
            print("Closing UI..." + str(caller) + str(threading.current_thread().ident))
            self.close_properties()
            self.is_showing_ui = False
            print("  -> Closed UI...")

        elif not self.is_showing_ui and self.should_be_showing_ui:
            print("showing UI: " + str(threading.current_thread().ident))
            self.show_properties()
            cv2.namedWindow(self.main_window_name)  # for mouse events
            self.mouse.attach_to_window(self.main_window_name)
            self.is_showing_ui = True

        if self.is_showing_ui:
            if self.busy is False:
                self.busy = True
                #imageprocessing.show(self.average_background_frame, "averagebg")

                imageprocessing.show(self.frame, self.main_window_name)

                imageprocessing.show(self.gaussian_blur_frame, "avg_bg_blurred")

                #imageprocessing.show(self.hue_frame, "hue_of_median")
                #imageprocessing.show(self.hue_as_bgr_frame, "hue_of_median2")
                #imageprocessing.show(self.sat_frame, "sat_of_median")
                #imageprocessing.show(self.lum_frame, "lum_of_median")

                #imageprocessing.show(self.limited_mask, "limited_mask")

                # imageprocessing.show(self.canny, "canny")
                #imageprocessing.show(self.difference_mask, 'diff_mask')

                show_masks = self.prop_value('ui/show_masks')
                if show_masks is True and self.last_colours is not None:
                    for colour in self.last_colours:
                        imageprocessing.show(colour.mask, 'mask_' + colour.name)
                self.busy = False

    def handle_ui(self):
        if self.is_showing_ui:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Pressed Quit")
                self.message_to_main_thread('quit')
            elif key == ord("s"):
                self.state.start("stabilize")
            elif key == ord("a"):
                self.state.start("average_background")
            elif key == ord("c"):
                self.state.start("calibrate")
            elif key == ord("b"):
                self.set_background_to_average_background()

    def show_ui(self, state=True):
        self.should_be_showing_ui = bool(state)

    def close_ui(self):
        self.show_ui(False)
        self.update_ui()
        self.handle_ui()

    def message_to_main_thread(self, message):
        self.main_thread_q.put(message)

    def message_from_queue(self, a_queue, timeout=0.001):
        try:
            msg = a_queue.get(True, timeout)  # check if we have a new image...
            return msg
        except queue.Empty:
            return None

    def perform_main_thread_events_and_check_if_need_to_quit(self):
        if threading.current_thread() is not threading.main_thread():
            print("function MUST be called from main thread")
            raise Exception

        # parse all messages...
        while True:
            msg = self.message_from_queue(
                self.main_thread_q)  # this blocks only for a small period, then times out if nothing.
            if msg is not None:
                if msg == 'frame':
                    self.update_ui()  # we execute this on the main thread.
                elif msg == 'quit':
                    self.close_ui()
                    return True
            else:  # no more messages to parse
                self.handle_ui()  # perfomr high gui functions
                return False

    def run(self):
        """
        Do not call directly use start instead.
        main loop to take care of all the processing

        this is a blocking call.
        """
        try:
            self.state.start('wait_for_first_frame')

            self.video_stream = self.start_video_stream()

            while self.thread_should_be_running:
                msg = self.message_from_queue(self.internal_message_queue)
                if msg is not None:
                    self.message_to_main_thread('frame')

        except Exception as ex:
            logging.error(traceback.format_exc())

        finally:

            self.video_stream.stop_and_wait_until_stopped()
            self.video_stream = None

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
            self.state.start("average_background")

    def prop_value(self, pathname):
        return self.properties.value_of(pathname)

    def start_average_background(self):
        print("start taking images of background")
        self.average_background_count = self.prop_value('tracker/averaged_frames')
        width, height = imageprocessing.resolution_of(self.frame)
        self.average_background_accumulator = imageprocessing.blank_image(width, height, 3, dtype=np.uint32)

    def start_calibrate(self):
        if self.average_background_frame is not None:
            balls = self.find_coloured_balls(self.average_background_frame)
            self.calibrate_fast_colour_tracked_from_coloured_balls(balls)

        self.state.start("normal")




    def run_average_background(self):
        if self.average_background_count > 0:
            deep = imageprocessing.convert_to_32bit_per_color_depth(self.sampling_frame)
            self.average_background_accumulator = imageprocessing.add(self.average_background_accumulator, deep)
            imageprocessing.draw_text(self.frame, str(self.average_background_count) +
                                      ' averaging', (5, 40), (255, 255, 255))
            self.average_background_count = self.average_background_count - 1
        else:
            width, height = imageprocessing.resolution_of(self.frame)
            self.average_background_frame = imageprocessing.blank_image(width, height, 3)
            d = imageprocessing.multiply(self.average_background_accumulator,
                                         1.0 / float(self.prop_value('tracker/averaged_frames')))

            cv2.convertScaleAbs(d, self.average_background_frame)  # convert to a normal BGR 8 bit image

            self.state.start("normal")

    def run_normal(self):
        self.frame = self.find_and_track_coloured_balls_in_frame(self.frame)

    def set_update_handler(self, handler):
        self.update_handler = handler

    def set_frame_handler(self, handler):
        self.frame_handler = handler

    def fire_frame_handler(self, frame_count):
        h = self.frame_handler
        if h is not None:
            h(frame_count)

    # requested by SOUND OF COLOUR
    def balls(self):
        return self.ball_tracker.balls

    def sample_colour(self, x, y, radius):
        hsv = imageprocessing.get_mean_hsv_from_circle_and_draw_debug(
            self.sampling_frame, (x, y), radius, self.frame)

        return hsv

    def sample_histogram(self, x, y, radius, image=None):
        if image is None:
            image = self.sampling_frame
        return imageprocessing.histogram_of_disc(
            image, (x, y), radius)

    def sample_histogram_hsv(self, x, y, radius):
        return imageprocessing.histogram_hsv_of_disc(
            self.sampling_frame_hsv, (x, y), radius)



if __name__ == '__main__':
    col = None
    try:
        col = ColouredBallTracker()
        col.show_ui(True)
        col.start()
        while True:
            if col.perform_main_thread_events_and_check_if_need_to_quit():  # handle all tracker event, including UI.
                break
    except KeyboardInterrupt:
        print("CRTL + C")
    finally:
        if col is not None:
            col.stop()
            col.wait_until_stopped()
