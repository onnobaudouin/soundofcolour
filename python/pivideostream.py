# this file should only be imported when running on RPI
from picamera.array import PiRGBArray
from picamera import PiCamera
from videostream import VideoStream


class PiVideoStream(VideoStream):
    def __init__(self, wanted_resolution, wanted_frame_rate, show_preview=True):
        super().__init__(wanted_resolution, wanted_frame_rate)
        self.camera = PiCamera()
        self.camera.resolution = wanted_resolution
        self.camera.framerate = wanted_frame_rate
        self.raw_capture = PiRGBArray(self.camera, size=wanted_resolution)
        if show_preview:  # preview runs at full speed, regardless...
            preview = self.camera.start_preview()
            preview.resolution = wanted_resolution
            preview.fullscreen = False
            preview.window = (40, 40) + wanted_resolution 
        self.stream = self.camera.capture_continuous(self.raw_capture,
                                                     format="bgr", use_video_port=True)
        self.name = "PiVideoStream"

    def update(self): # this is main loop of the thread...
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

    def on_start_stabilize(self):
        self.camera.exposure_mode = 'auto'
        self.camera.awb_mode = "auto"  # PiCamera.AWB_MODES, aslo awb_gain

    def on_stop_stabilize(self):
        gains = self.camera.awb_gains
        self.camera.awb_mode = "off"
        self.camera.awb_gains = gains
        self.camera.exposure_mode = 'off'

if __name__ == '__main__':
    import sys
    import threading
    from framespersecond import FramesPerSecond
    
    fps = FramesPerSecond()
    stop_adjustment = 10
    seconds = 0

    def image_handler():
        global seconds
        new_frame, last_valid_frame, frame_count, resolution = vs.latest()
        if new_frame is not None:
            if fps.add():
                seconds = seconds + 1
                print("Image received on thread: " + str(threading.current_thread().ident))
                vs.print_stats()
                if seconds == stop_adjustment:
                    vs.on_stop_stabilize()
                    

    vs = None
    try:
        should_be_running = True
        print("Starting program on thread: "+str(threading.current_thread().ident))
        vs = PiVideoStream((400, 304), 60)
        vs.on_frame(image_handler)
        vs.flip_horizontal()
        vs.start()
        vs.on_start_stabilize()
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
