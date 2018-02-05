# import the necessary packages
import cv2
from videostream import VideoStream


class OpenCVVideoStream(VideoStream):
    def __init__(self, wanted_resolution, wanted_frame_rate, open_cv_src=0):
        super().__init__(wanted_resolution, wanted_frame_rate)
        self.wait_time_after_start = 0.0  # we don't wait with open cv

        self.stream = cv2.VideoCapture(open_cv_src)
        width, height = wanted_resolution
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_FPS, wanted_frame_rate)  # doesn't work on web cam

        self.name = "OpenCVVideoStream"

    def update(self):
        while self.thread_should_be_running:
            # otherwise, read the next frame from the stream
            (captured_and_ready, frame) = self.stream.read()
            self.set_frame(frame, captured_and_ready)


