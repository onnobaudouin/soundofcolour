from Hardware import *
import MouseInteraction as mouse
from Colour import Colour
import OpenCVHelpers as cvh
from framespersecond import FramesPerSecond

from videostream import VideoStream
from BallTracker import BallTracker
from OctaveGrid import OctaveGrid
from soundsocketserver import SoundSocketServer
from simplewebserver import *
from web import *
from propertiesopencvui import *
from transitions import Machine  # https://github.com/pytransitions/transitions


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

    def start_state(self, new_state):
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
            colour.add('min_hsv', PropType.hsv)
            colour.add('max_hsv', PropType.hsv)
        return props

    def update_resolution(self, resolution):
        print("updating to resolution: " + str(resolution))
        width, height = resolution
        self.grid = OctaveGrid(width, height, padding=10, divisions_x=10, divisions_y=2)
        pass

    def update(self):
        vs = self.video_stream
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            # on resolution confirmation / change
            if not self.has_received_first_valid_frame:
                self.update_resolution(resolution)
                self.has_received_first_valid_frame = True

            # original = cvh.clone_image(new_frame) # only needed when masking colours!

            if self.state == 'stabilize':
                if vs.is_stabilizing:
                    cvh.draw_text(new_frame, str(vs.stabilize_frame_counter) +
                                  ' stabilising', (5, 40), (255, 255, 255))
                else:
                    self.start_state('normal')

            # print("frame: " + str(frame_count) +
            #       ' fps:' + str(self.video_stream.frames_per_second.fps) +
            #       'bounced: ' + str(self.video_stream.duplicate_frames_per_second_requests.fps))
            cv2.imshow(self.main_window_name, new_frame)

    def run(self):
        self.show_properties()
        try:
            self.video_stream = self.start_video_stream()
            cv2.namedWindow(self.main_window_name)  # for mouse events
            self.start_state('stabilize')  # todo: wrap in state machine
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
