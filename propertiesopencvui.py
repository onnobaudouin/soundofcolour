from properties import *
import cv2


class PropertiesOpenCVUI(PropertiesListener):
    def __init__(self, properties_obj):
        self.properties = properties_obj
        self.properties.add_listener(self)
        self.state = None
        self.properties_uis = dict()

    def on_prop_updated(self, prop: PropertyNode, from_runtime_change: bool=True):
        self.update_ui(prop.path_as_str())

    def nothing(self, x):
        pass

    def bar_call_back(self, prop: Property, value, index=None):

        if self.state == "LOADING":
            return
        print("ui - callback: " + prop.name + " : " + str(value))
        if prop.type == PropNodeType.hsv:
            if index == 0:
                prop.set(float(value), index)
            else:
                prop.set(float(value) / 255.0, index)
        else:
            prop.set(value, index)

    def create_bar(self, prop: Property, prop_name: str, window_name: str, minimum, maximum, callback, index=None):
        if callback is None:
            callback = self.nothing
        # print("Creating Bar...")
        cv2.createTrackbar(prop_name, window_name, minimum, maximum, callback)

        # keep track of UI elements...
        path = prop.path_as_str()

        if path not in self.properties_uis:
            self.properties_uis[path] = []
        self.properties_uis[path].append(dict(
            name=prop_name,
            window_name=window_name,
            index=index
        ))

    def set_bar_pos(self, prop_name, window_name, value):
        current_value = self.get_bar_pos(prop_name, window_name)
        if current_value != value:
            cv2.setTrackbarPos(prop_name, window_name, value)

    def get_bar_pos(self, prop_name, window_name):
        return cv2.getTrackbarPos(prop_name, window_name)

    def show(self, node_path: str):
        #
        # print("show "+node_path)
        self.state = "LOADING"
        node = self.properties.node_at_path(node_path)
        if isinstance(node, Properties):
            window_name = node_path
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # todo: better name in json?
            for prop in node.child_nodes():
                if prop.type == PropNodeType.rgb:
                    for i in range(0, len(prop.min)):
                        self.create_bar(prop, prop.name + '_' + prop.names[i],
                                        window_name, prop.min[i], prop.max[i],
                                        lambda x, p=prop, index=i: self.bar_call_back(p, x, index), i)
                elif prop.type == PropNodeType.hsv:
                    self.create_bar(prop, prop.name + '_' + prop.names[0],
                                    window_name, int(prop.min[0]), int(prop.max[0]),
                                    lambda x, p=prop, index=0: self.bar_call_back(p, x, index), 0)
                    for i in range(1, 3):
                        self.create_bar(prop, prop.name + '_' + prop.names[i],
                                        window_name, int(prop.min[i] * 255.0), int(prop.max[i] * 255.0),
                                        lambda x, p=prop, index=i: self.bar_call_back(p, x, index), i)
                elif prop.type == PropNodeType.unsigned_int:
                    self.create_bar(prop, prop.name, window_name, prop.min, prop.max,
                                    lambda x, p=prop: self.bar_call_back(p, x))
                elif prop.type == PropNodeType.bool:
                    self.create_bar(prop, prop.name, window_name, 0, 1, lambda x, p=prop: self.bar_call_back(p, x))
        self.update_ui(node_path)
        self.state = None

    def update_ui(self, node_path: str):
        # print("update_ui : "+node_path)
        node = self.properties.node_at_path(node_path)
        path = node.path_as_str()
        if path in self.properties_uis:
            uis_for_node = self.properties_uis[path]
            for ui in uis_for_node:
                name = ui["name"]
                window_name = ui["window_name"]
                index = ui['index']
                if node.type == PropNodeType.hsv:
                    if index == 0:
                        self.set_bar_pos(name, window_name, int(node.value()[index]))
                    else:
                        self.set_bar_pos(name, window_name, int(node.value()[index] * 255.0))
                elif node.type == PropNodeType.rgb:
                    self.set_bar_pos(name, window_name, node.value()[index])
                else:
                    self.set_bar_pos(name, window_name, node.value())
        else:
            if node.type == PropNodeType.group:
                for prop in node.child_nodes():
                    self.update_ui(prop.path_as_str())

    def close(self):
        cv2.destroyAllWindows()
        self.properties_uis = dict()
