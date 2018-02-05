# this file should only be imported when running on RPI
from picamera.array import PiRGBArray
from picamera import PiCamera
from python.videostream import VideoStream


class PiVideoStream(VideoStream):
    def __init__(self, wanted_resolution, wanted_frame_rate):
        super().__init__(wanted_resolution, wanted_frame_rate)
        self.camera = PiCamera()
        self.camera.resolution = wanted_resolution
        self.camera.framerate = wanted_frame_rate
        self.raw_capture = PiRGBArray(self.camera, size=wanted_resolution)

        self.stream = self.camera.capture_continuous(self.raw_capture,
                                                     format="bgr", use_video_port=True)

    def update(self):
        for frame in self.stream:  # todo check if we need to use 'with'
            if self.thread_should_be_running:
                self.set_frame(frame.array)
                self.raw_capture.truncate(0)
            else:
                self.stream.close()
                self.raw_capture.close()
                self.camera.close()
                return  # exits for loop and end thread

    def flip_horizontal(self, flip=True):
        self.camera.hflip = flip

    # def resolution(self):
    #   return self.camera.resolution

    def on_start_stabilize(self):
        self.camera.exposure_mode = 'auto'
        self.camera.awb_mode = "auto"  # PiCamera.AWB_MODES, aslo awb_gain

    def on_stop_stabilize(self):
        gains = self.camera.awb_gains
        self.camera.awb_mode = "off"
        self.camera.awb_gains = gains
        self.camera.exposure_mode = 'off'

