from properties import *
import cv2


class PropertiesOpenCVUI:
    def __init__(self, properties_obj):
        self.properties = properties_obj

    def nothing(self, x):
        pass

    def show(self, node_path):
        node = self.properties.node_from_path(node_path)
        if isinstance(node, Properties):
            props = node.props
            name = node_path
            cv2.namedWindow(name)  # todo: better name in json?
            for prop_key in props:
                prop = props[prop_key]
                if prop.type == PropType.hsv:
                    cv2.createTrackbar(prop.name + '_hue', name, prop.min[0], prop.max[0], self.nothing)
                    cv2.createTrackbar(prop.name + '_sat', name, prop.min[1], prop.max[1], self.nothing)
                    cv2.createTrackbar(prop.name + '_lum', name, prop.min[2], prop.max[2], self.nothing)
                if prop.type == PropType.rgb:
                    cv2.createTrackbar(prop.name + '_red', name, prop.min[0], prop.max[0], self.nothing)
                    cv2.createTrackbar(prop.name + '_green', name, prop.min[1], prop.max[1], self.nothing)
                    cv2.createTrackbar(prop.name + '_blue', name, prop.min[2], prop.max[2], self.nothing)
                if prop.type == PropType.unsigned_int:
                    cv2.createTrackbar(prop.name, name, prop.min, prop.max, self.nothing)
                if prop.type == PropType.bool:
                    cv2.createTrackbar(prop.name, name, 0, 1, self.nothing)

