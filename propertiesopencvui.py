from properties import *
import cv2


class PropertyUIOpenCV:
    def __init__(self, name: str, window_name: str):
        self.name = name
        self.window_name = window_name
        self.children = []

    def add(self, ui: "PropertyUIOpenCV"):
        self.children.append(ui)


class PropertiesOpenCVUI(PropertiesListener):
    def __init__(self, properties_obj):
        self.properties = properties_obj
        self.properties.add_listener(self)
        self.state = None
        self.properties_uis = dict()

    def on_prop_updated(self, prop: PropertyNode, from_runtime_change: bool = True):
        """
        Called when a property value is changed - implements PropertiesListener
        :param prop:
        :param from_runtime_change:
        :return:
        """
        self.update_ui(prop.path_as_str())

    def set_bar_pos(self, prop_name, window_name, value):
        current_value = self.get_bar_pos(prop_name, window_name)
        if current_value != value:
            cv2.setTrackbarPos(prop_name, window_name, value)

    def get_bar_pos(self, prop_name, window_name):
        return cv2.getTrackbarPos(prop_name, window_name)

    def bar_call_back(self, prop: Property, ui: PropertyUIOpenCV):
        if self.state == "SILENT":
            return
        prop.set(self.get_value_from_ui(prop, ui))

    def create_ui_bar(self, ui: PropertyUIOpenCV, prop: Property, min, max, prop_ui=None):
        callback_ui = ui
        if prop_ui is not None:
            callback_ui = prop_ui
        cv2.createTrackbar(ui.name, ui.window_name, min, max,
                           lambda x, p=prop, ui=callback_ui: self.bar_call_back(p, ui))

    def ui_for_rgb(self, prop: Property, window_name: str) -> PropertyUIOpenCV:
        ui = PropertyUIOpenCV(prop.name, window_name)
        for i in range(0, len(prop.min)):
            child_ui = PropertyUIOpenCV(prop.name + '_' + prop.names[i], window_name)
            ui.add(child_ui)
            self.create_ui_bar(child_ui, prop, prop.min[i], prop.max[i], ui)
        return ui

    def ui_for_hsv(self, prop: Property, window_name: str) -> PropertyUIOpenCV:
        ui = PropertyUIOpenCV(prop.name, window_name)
        for i in range(0, len(prop.min)):
            child_ui = PropertyUIOpenCV(prop.name + '_' + prop.names[i], window_name)
            ui.add(child_ui)
            max = int(prop.max[i])
            if i > 0:
                max = int(max * 255)  # S/V are 0 to 1 so we map to 0 -> 255, can be anythoing though... 100?
            self.create_ui_bar(child_ui, prop, int(prop.min[i]), max, ui)
        return ui

    def ui_for_prop(self, prop: Property, window_name: str) -> PropertyUIOpenCV:
        ui = PropertyUIOpenCV(prop.name, window_name)
        self.create_ui_bar(ui, prop, prop.min, prop.max)
        return ui

    def create_ui_for_property(self, prop: Property, window_name) -> PropertyUIOpenCV:
        if prop.type == PropNodeType.rgb:
            ui = self.ui_for_rgb(prop, window_name)
        elif prop.type == PropNodeType.hsv:
            ui = self.ui_for_hsv(prop, window_name)
        else:
            ui = self.ui_for_prop(prop, window_name)
        return ui

    def show(self, node_path: str):
        # todo: prevent double showing?
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

    def get_uis_for_property(self, prop: Property):
        path = prop.path_as_str()
        if path in self.properties_uis:
            return self.properties_uis[path]
        return None

    def add_ui_for_property(self, prop: Property, ui: PropertyUIOpenCV):
        # keep track of UI elements...
        path = prop.path_as_str()
        if path not in self.properties_uis:
            self.properties_uis[path] = []
        self.properties_uis[path].append(ui)

    def set_bar_pos_for_ui(self, ui: PropertyUIOpenCV, value):
        self.set_bar_pos(ui.name, ui.window_name, value)

    def get_bar_pos_for_ui(self, ui: PropertyUIOpenCV):
        return self.get_bar_pos(ui.name, ui.window_name)

    def ui_values_from_ui_children(self, ui: PropertyUIOpenCV, prop: Property) -> List:
        p = []
        for i in range(0, len(prop.min)):
            p.append(self.get_bar_pos_for_ui(ui.children[i]))
        return p

    def set_ui_values_for_ui_children(self, ui: PropertyUIOpenCV, ui_values):
        for i in range(0, len(ui.children)):
            self.set_bar_pos_for_ui(ui.children[i], ui_values[i])

    def get_value_from_ui(self, prop: Property, ui: PropertyUIOpenCV):
        if prop.type == PropNodeType.hsv:
            ui_values = self.ui_values_from_ui_children(ui, prop)
            return float(ui_values[0]), float(ui_values[1]) / 255.0, float(ui_values[2]) / 255.0
        elif prop.type == PropNodeType.rgb:
            ui_values = self.ui_values_from_ui_children(ui, prop)
            return int(ui_values[0]), int(ui_values[1]), int(ui_values[2])
        else:
            return self.get_bar_pos_for_ui(ui)

    def update_value_for_ui(self, prop: Property, ui: PropertyUIOpenCV):
        """
        This function updates the UI for a given property. It will NOT set the property and is
        garantueed not to have side effects.
        :param prop:
        :param ui:
        :return:
        """
        current_state = self.state
        self.state = "SILENT"  # prevent HIGHGUI from sending us an update that the ui has changed..
        if prop.type == PropNodeType.hsv:
            prop_value = prop.value()
            ui_values = [int(prop_value[0]), int(prop_value[1] * 255.0), int(prop_value[2] * 255.0)]
            self.set_ui_values_for_ui_children(ui, ui_values)
        elif prop.type == PropNodeType.rgb:
            self.set_ui_values_for_ui_children(ui, [int(i) for i in prop.value()])
        else:
            self.set_bar_pos_for_ui(ui, prop.value())
        self.state = current_state

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
