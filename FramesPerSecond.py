import cv2


class FramesPerSecond:
    def __init__(self):
        self.frame_count = 0
        self.last_time = FramesPerSecond.get_time()
        self.fps = 0

    @staticmethod
    def get_time():
        return cv2.getTickCount()
        # return time.perf_counter()

    @staticmethod
    def time_difference_in_seconds(last, new):
        delta = new - last
        return delta / cv2.getTickFrequency()

    def add(self):
        self.frame_count = self.frame_count + 1
        new_time = FramesPerSecond.get_time()
        time = FramesPerSecond.time_difference_in_seconds(self.last_time, new_time)
        if time > 1.0:
            self.fps = int(self.frame_count / time)
            # print(str(self.fps))  # FPS
            self.last_time = new_time
            self.frame_count = 0
            return True
        return False    
