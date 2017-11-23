# import the necessary packages
from threading import Thread
import cv2
from FramesPerSecond import FramesPerSecond


class WebcamVideoStream:
    def __init__(self, src=0, resolution=(320, 240), framerate=30):
        # initialize the video camera stream and read the first frame
        # from the stream
        self.stream = cv2.VideoCapture(src)

        width, height = resolution

        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.stream.set(cv2.CAP_PROP_FPS, framerate)  # doesn't work on webcam

        # (self.grabbed, self.frame) = self.stream.read()
        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False
        self.frame = None
        self.frame_count = 0
        self.fps = FramesPerSecond()

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, read the next frame from the stream
            (captured_and_ready, frame) = self.stream.read()
            if not captured_and_ready:
                self.frame = None
                continue

            self.frame_count = self.frame_count + 1
            self.frame = frame
            self.fps.add()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
