from JSON import JSON
import numpy as np

class Colour:
    def __init__(self, name, low=[0, 0, 0], high=[255, 255, 255], rgb=[255, 255, 255]):
        self.name = name
        self.low = low
        self.high = high
        self.low_as_numpy = self.as_numpy(self.low)
        self.high_as_numpy = self.as_numpy(self.high)
        self.contours = None
        self.mask = None
        self.rgb = rgb
        # self.update(self.low, self.high)

    def load_from_file(self):
        data = JSON.load(self.filename())
        if data is not None:
            self.update(data['low'], data['high'])

    def save_to_file(self):
        JSON.save(self.filename(),
                  {
                      "low": self.low,
                      "high": self.high
                  }
                  )

    def filename(self):
        return self.name + '.json'

    def as_numpy(self, hsv_as_array):
        return np.array(hsv_as_array)

    def update(self, low, high):
        save = False
        if low != self.low:
            self.low = low
            self.low_as_numpy = self.as_numpy(self.low)
            save = True
        if high != self.high:
            self.high = high
            self.high_as_numpy = self.as_numpy(self.high)
            save = True
        if save:
            self.save_to_file()