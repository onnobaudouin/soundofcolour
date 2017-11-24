from properties import *
from functools import partial
import cv2


class PropertiesOpenCVUI:
    def __init__(self, properties_obj):
        self.properties = properties_obj

    def nothing(self, x):
        pass
    
    def barCallBack(self, prop, value, index=None):
        
        prop.set(value, index)
        
        
    def createBar(self,prop_name, window_name, minimum, maximum, callback):
        if callback is None:
            callback = self.nothing
        cv2.createTrackbar(prop_name, window_name, minimum, maximum, callback)
    
    def setBarPos(elf, prop_name, window_name, value):
        cv2.setTrackbarPos(prop_name, window_name, value)    
        

    def show(self, node_path):
        node = self.properties.node_from_path(node_path)
        if isinstance(node, Properties):
            props = node.props
            window_name = node_path
            cv2.namedWindow(window_name)  # todo: better name in json?
            for prop_key in props:
                prop = props[prop_key]
                if prop.type in [PropType.hsv, PropType.rgb]:
                    for i in range(0, len(prop.min)):
                        self.createBar(prop.name + '_' + prop.names[i], 
                            window_name, prop.min[i], prop.max[i], lambda x: self.barCallBack(prop, x, i))
                if prop.type == PropType.unsigned_int:
                    self.createBar(prop.name, window_name, prop.min, prop.max, lambda x: self.barCallBack(prop, x))
                if prop.type == PropType.bool:
                    self.createBar(prop.name, window_name, 0, 1, lambda x: self.barCallBack(prop, x))
        self.update(node_path)

    def update(self, node_path):
        node = self.properties.node_from_path(node_path)
        if isinstance(node, Properties):
            props = node.props
            window_name = node_path
            for prop_key in props:
                prop = props[prop_key]
                if prop.type in [PropType.hsv, PropType.rgb]:
                    for i in range(0, len(prop.min)):
                        self.setBarPos(prop.name + '_' + prop.names[i], window_name, prop.value()[i])
                else:
                    self.setBarPos(prop.name, window_name, prop.value())
                   
