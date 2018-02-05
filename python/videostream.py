from framespersecond import FramesPerSecond
from threading import Thread
import time
import imageprocessing as imageprocessing
from queue import Queue


class VideoStream:
    def __init__(self, wanted_resolution=(320, 240), wanted_frame_rate=30):
        print("Starting VideoStream: " + str(wanted_resolution) + ' ' + str(wanted_frame_rate))
        self.wanted_resolution = wanted_resolution
        self.wanted_frame_rate = wanted_frame_rate

        self.frame = None
        self.frame_count = 0
        self.new_frame_available = False
        self.frames_per_second = FramesPerSecond()
        self.duplicate_frames_per_second_requests = FramesPerSecond()
        self.wait_time_after_start = 2.0
        self.actual_resolution = None
        self.stabilize_frame_counter = 0
        self.is_stabilizing = False
        self.thread = None
        self.thread_should_be_running = False

        self.on_frame_handler = None
        self.message_q = Queue()
        self.name = "VideoStream"

    def update_stats(self):
        self.frame_count = self.frame_count + 1
        self.frames_per_second.add()

    def start(self):
        if self.thread is not None:
            print("Video Stream already running, ignored request")
            return
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread_should_be_running = True
        self.thread.name = self.name + " Thread"
        self.thread.start()
        print(self.name + " Main Loop Thread: " + str(self.thread.ident))
        # print("Waiting for Video Stream to initialize:" + str(self.wait_time_after_start) + 's')
        time.sleep(self.wait_time_after_start)  # stabilize - recommended practice
        return self

    def update(self):
        # process each frame
        raise NotImplementedError

    def start_stabilize(self, frames=30):
        self.stabilize_frame_counter = frames
        self.is_stabilizing = True
        self.on_start_stabilize()

    def update_stabilize(self):
        if self.is_stabilizing:
            self.stabilize_frame_counter = self.stabilize_frame_counter - 1
            if self.stabilize_frame_counter == 0:
                self.is_stabilizing = False
                self.on_stop_stabilize()

    def on_start_stabilize(self):
        print("warning: no automatic mode to stabilize supported... stabilize will depend on camera settings in OS")
        pass

    def on_stop_stabilize(self):
        pass

    def latest(self):
        # return the frame most recently read or None if not changed
        if self.new_frame_available:
            self.new_frame_available = False
            return self.frame, self.frame, self.frame_count, imageprocessing.resolution_of(self.frame)
        else:
            self.duplicate_frames_per_second_requests.add()
            return None, self.frame, self.frame_count, imageprocessing.resolution_of(self.frame)

    def stop_and_wait_until_stopped(self):
        if self.thread is None:
            print("Video Stream is already stopped - ignored")
            return
        # stop the thread and release any resources
        print("stopping video stream blocking......")
        self.thread_should_be_running = False
        self.thread.join()
        print('Closed: '+self.name + " Main Loop Thread: " + str(self.thread.ident))
        self.thread = None



    def set_frame(self, frame, is_new_frame=True):
        if frame is None:
            print("Error a frame was set to None")
        else:
            self.frame = frame
            self.actual_resolution = imageprocessing.resolution_of(frame)
            if self.actual_resolution != self.wanted_resolution:
                print("actual resolution is not same as wanted_resolution, adjusting... " +
                      str(self.actual_resolution) + ' wanted:' + str(self.wanted_resolution))
            self.new_frame_available = True
            self.notify_new_frame()
            self.update_stats()
            self.update_stabilize()

    def notify_new_frame(self):
        if self.on_frame_handler is not None:
            self.on_frame_handler()

        self.message_q.put('frame')



    def flip_horizontal(self):
        raise NotImplementedError

    def resolution(self):
        return self.wanted_resolution

    def on_frame(self, handler):
        self.on_frame_handler = handler

    @staticmethod
    def create(wanted_resolution=(320, 240), wanted_frame_rate=32, use_pi_camera=False, open_cv_src=0):
        if use_pi_camera:
            from pivideostream import PiVideoStream
            print("Using Pi Video Stream")
            return PiVideoStream(wanted_resolution=wanted_resolution,
                                 wanted_frame_rate=wanted_frame_rate)
        else:
            from opencvvideostream import OpenCVVideoStream
            print("Using OpenCV Video Stream, src:" + str(open_cv_src))
            return OpenCVVideoStream(wanted_resolution=wanted_resolution,
                                     wanted_frame_rate=wanted_frame_rate, open_cv_src=open_cv_src)


if __name__ == '__main__':
    import sys
    import signal
    import threading


    should_be_running = True



    def handler(signum, frame):
        global should_be_running
        print("Received SIGNTREM: "+str(signum))
        should_be_running = False

    vs = None
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    def image_handler():
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            print("Image received on thread: " + str(threading.current_thread().ident))
            print(" frame: " + str(frame_count) +
                  ' fps:' + str(vs.frames_per_second.fps) +
                  ' bounced: ' + str(vs.duplicate_frames_per_second_requests.fps))


    try:
        print("Starting program on thread: "+str(threading.current_thread().ident))
        vs = VideoStream.create()
        vs.on_frame(image_handler)
        vs.start()
        while should_be_running:
            what = str(input("Press Q to stop"))
            if what.upper() == "Q":
                should_be_running = False


    except KeyboardInterrupt:
        print("CRTL + C")
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        if vs is not None:
            vs.stop_and_wait_until_stopped()
