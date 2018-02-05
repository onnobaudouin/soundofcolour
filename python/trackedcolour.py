class TrackedColour:
    def __init__(self, name, minimum_hsv, maximum_hsv, rgb):
        self.name = name
        self.minimum_hsv = minimum_hsv
        self.maximum_hsv = maximum_hsv
        self.mask = None
        self.rgb = rgb
        self.min_values = None
        self.max_values = None
