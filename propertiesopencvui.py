from properties import *
import cv2


class PropertiesOpenCVUI(PropertiesListener):
    def __init__(self, properties_obj):
        self.properties = properties_obj
        self.properties.add_listener(self)
        self.state = None
        self.properties_uis = dict()

    def on_prop_updated(self, prop: PropertyNode, from_runtime_change: bool = True):
        self.update_ui(prop.path_as_str())

    def nothing(self, x):
        pass

    def create_bar(self, prop_name: str, window_name: str, minimum, maximum, callback):
        if callback is None:
            callback = self.nothing
        cv2.createTrackbar(prop_name, window_name, minimum, maximum, callback)

    def set_bar_pos(self, prop_name, window_name, value, silent=False):
        current_value = self.get_bar_pos(prop_name, window_name)
        if current_value != value:
            # todo - detach event handler that will trigger this. we do not really want to be notified...
            current_state = self.state
            if silent:
                self.state = "SILENT"

            cv2.setTrackbarPos(prop_name, window_name, value)

            self.state = current_state


    def get_bar_pos(self, prop_name, window_name):
        return cv2.getTrackbarPos(prop_name, window_name)

    def prop_call_back(self, prop: Property, ui):
        # lets NOT read individuals but read the whole prop.
        #if self.state == "LOADING":
        #    return
        if self.state == "SILENT":
            return
        prop.set(self.get_value_from_ui(prop, ui))


    def create_ui_for_property(self, prop: Property, window_name):
        if prop.type == PropNodeType.rgb:
            ui = dict(name=prop.name, window_name=window_name, children_ui=[])  # composite UI
            for i in range(0, len(prop.min)):
                child_ui = dict(name=prop.name + '_' + prop.names[i], window_name=window_name)
                ui["children_ui"].append(child_ui)
                self.create_bar(child_ui["name"], child_ui["window_name"], prop.min[i], prop.max[i],
                                lambda x, p=prop, ui=ui: self.prop_call_back(p, ui))
        elif prop.type == PropNodeType.hsv:
            ui = dict(name=prop.name, window_name=window_name, children_ui=[])  # composite UI
            for i in range(0, len(prop.min)):
                child_ui = dict(name=prop.name + '_' + prop.names[i], window_name=window_name)
                ui["children_ui"].append(child_ui)
                min = int(prop.min[i])
                max = int(prop.max[i])
                if i > 0:
                    max = int(max * 255)  # S/V are 0 to 1 so we map to 0 -> 255, can be anythoing though... 100?
                self.create_bar(child_ui["name"], child_ui["window_name"], min, max,
                                lambda x, p=prop, ui=ui: self.prop_call_back(p, ui))
        else:
            ui = dict(name=prop.name, window_name=window_name)
            self.create_bar(ui["name"], ui["window_name"], prop.min, prop.max,
                            lambda x, p=prop, ui=ui: self.prop_call_back(p, ui))
        return ui

    def show(self, node_path: str):
        #
        # print("show "+node_path)
        # self.state = "LOADING"
        node = self.properties.node_at_path(node_path)
        if isinstance(node, Properties):
            window_name = node_path
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # todo: better name in json?
            for prop in node.child_nodes():
                if prop.type != PropNodeType.group:
                    ui = self.create_ui_for_property(prop, window_name)
                    self.add_ui_for_property(prop, ui)
                else:
                    print("Cannot show SUB groups in OPEN_CV...")


        self.update_ui(node_path)
        # self.state = None

    def get_uis_for_property(self, prop: Property):
        path = prop.path_as_str()
        if path in self.properties_uis:
            return self.properties_uis[path]
        return None

    def add_ui_for_property(self, prop: Property, ui):
        # keep track of UI elements...
        path = prop.path_as_str()
        if path not in self.properties_uis:
            self.properties_uis[path] = []
        self.properties_uis[path].append(ui)

    def get_value_from_ui(self, prop: Property, ui):
        if prop.type == PropNodeType.hsv:
            children_ui = ui["children_ui"]
            h = float(self.get_bar_pos(children_ui[0]["name"], children_ui[0]["window_name"]))
            s = float(self.get_bar_pos(children_ui[1]["name"], children_ui[1]["window_name"])) / 255.0
            v = float(self.get_bar_pos(children_ui[2]["name"], children_ui[2]["window_name"])) / 255.0
            return h, s, v
        elif prop.type == PropNodeType.rgb:
            children_ui = ui["children_ui"]
            r = int(self.get_bar_pos(children_ui[0]["name"], children_ui[0]["window_name"]))
            g = int(self.get_bar_pos(children_ui[1]["name"], children_ui[1]["window_name"]))
            b = int(self.get_bar_pos(children_ui[2]["name"], children_ui[2]["window_name"]))
            return r, g, b  # todo: list to tuple.
        else:
            return self.get_bar_pos(ui["name"], ui["window_name"])

    def update_value_for_ui(self, prop: Property, ui):
        if prop.type == PropNodeType.hsv:
            children_ui = ui["children_ui"]
            self.set_bar_pos(children_ui[0]["name"], children_ui[0]["window_name"], int(prop.value()[0]), True)
            self.set_bar_pos(children_ui[1]["name"], children_ui[1]["window_name"], int(prop.value()[1] * 255.0), True)
            self.set_bar_pos(children_ui[2]["name"], children_ui[2]["window_name"], int(prop.value()[2] * 255.0), True)
        elif prop.type == PropNodeType.rgb:
            children_ui = ui["children_ui"]
            for i in range(0, 2):
                self.set_bar_pos(children_ui[i]["name"], children_ui[i]["window_name"], int(prop.value()[i]), True)
        else:
            self.set_bar_pos(ui["name"], ui["window_name"], prop.value(), True)

    def update_ui(self, node_path: str):
        # print("update_ui : "+node_path)
        node = self.properties.node_at_path(node_path)
        if node.type == PropNodeType.group:
            for sub_node in node.child_nodes():
                self.update_ui(sub_node.path_as_str())
        else:
            uis_for_node = self.get_uis_for_property(node)
            if uis_for_node is not None:
                for ui in uis_for_node:
                    self.update_value_for_ui(node, ui)

    def close(self):
        cv2.destroyAllWindows()
        self.properties_uis = dict()
