from properties import *
import cv2


class PropertiesOpenCVUI:
    def __init__(self, properties_obj):
        self.properties = properties_obj
        self.state = None

    def nothing(self, x):
        pass

    #  @staticmethod
    def bar_call_back(self, prop, value, index=None):
        runtime_change = self.state is None
        prop.set(value, index, from_runtime_change=runtime_change)
        self.properties.update_permanent_storage()  # todo: this should be called from within properties

    def create_bar(self, prop_name, window_name, minimum, maximum, callback):
        if callback is None:
            callback = self.nothing
        cv2.createTrackbar(prop_name, window_name, minimum, maximum, callback)

    def set_bar_pos(self, prop_name, window_name, value):
        cv2.setTrackbarPos(prop_name, window_name, value)

    def show(self, node_path):
        self.state = "LOADING"
        node = self.properties.node_at_path(node_path)
        if isinstance(node, Properties):
            # props = node.children
            window_name = node_path
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # todo: better name in json?
            for prop in node.child_nodes():
                # prop = props[prop_key]
                if prop.type in [PropNodeType.hsv, PropNodeType.rgb]:
                    for i in range(0, len(prop.min)):
                        self.create_bar(prop.name + '_' + prop.names[i],
                                        window_name, prop.min[i], prop.max[i],
                                        lambda x, p=prop, index=i: self.bar_call_back(p, x, index))
                elif prop.type == PropNodeType.unsigned_int:
                    self.create_bar(prop.name, window_name, prop.min, prop.max,
                                    lambda x, p=prop: self.bar_call_back(p, x))
                elif prop.type == PropNodeType.bool:
                    self.create_bar(prop.name, window_name, 0, 1, lambda x, p=prop: self.bar_call_back(p, x))
        self.update(node_path)
        self.state = None

    def update(self, node_path):
        node = self.properties.node_at_path(node_path)
        if isinstance(node, Properties):
            window_name = node_path
            for prop in node.child_nodes():
                if prop.type in [PropNodeType.hsv, PropNodeType.rgb]:
                    for i in range(0, len(prop.min)):
                        self.set_bar_pos(prop.name + '_' + prop.names[i], window_name, prop.value()[i])
                else:
                    self.set_bar_pos(prop.name, window_name, prop.value())

    def close(self):
        cv2.destroyAllWindows()
