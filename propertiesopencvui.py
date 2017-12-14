from properties import *
import cv2


class PropertyUIOpenCV:
    STATE = None

    def __init__(self, window_name: str, prop: Property, name: str = None, min=None, max=None, callback_ui=None,
                 visual=True):
        if name is None:
            name = prop.name
        self.name = name
        self.window_name = window_name
        self.prop = prop

        self.min = prop.min
        self.max = prop.max
        if min is not None:
            self.min = min
        if max is not None:
            self.max = max
        self.min_ui = self.prop_to_ui(self.min)
        self.max_ui = self.prop_to_ui(self.max)

        if callback_ui is None:
            callback_ui = self
        if visual is True:
            cv2.createTrackbar(self.name, self.window_name, self.min_ui, self.max_ui,
                               lambda x, ui=callback_ui: self.bar_call_back(ui))

    def bar_call_back(self, ui: "PropertyUIOpenCV"):
        if PropertyUIOpenCV.STATE == "SILENT":
            return
        self.prop.set(ui.ui_to_prop(ui.ui_value()))

    def sync_ui_to_prop(self):
        PropertyUIOpenCV.STATE = "SILENT"
        self.set_ui_value(self.prop_to_ui(self.prop.value()))
        PropertyUIOpenCV.STATE = None

    def ui_value(self):
        return cv2.getTrackbarPos(self.name, self.window_name)

    def set_ui_value(self, value):
        current_value = self.ui_value()
        if current_value != value:
            cv2.setTrackbarPos(self.name, self.window_name, value)

    def prop_to_ui(self, prop_value):
        return int(prop_value)

    def ui_to_prop(self, ui_value):
        return int(ui_value)


class PropertyUIMultipleOpenCV(PropertyUIOpenCV):
    def __init__(self, window_name: str, prop: Property):
        super().__init__(window_name, prop, visual=False)
        self.children = [self.create_child(i) for i in range(0, len(prop.min))]

    def create_child(self, index):
        return PropertyUIOpenCV(self.window_name,
                                self.prop,
                                self.prop.name + '_' + self.prop.names[index],
                                self.min_ui[index],
                                self.max_ui[index],
                                self, visual=True)

    def set_ui_value(self, value):
        for i, child_ui in enumerate(self.children):  # a zip might work too
            child_ui.set_ui_value(value[i])

    def ui_value(self):
        return [child.ui_value() for child in self.children]


class PropertyUIRGBOpenCV(PropertyUIMultipleOpenCV):
    def __init__(self, window_name: str, prop: Property):
        super().__init__(window_name, prop)

    def prop_to_ui(self, prop_value):
        return [int(i) for i in prop_value]

    def ui_to_prop(self, ui_value):
        return int(ui_value[0]), int(ui_value[1]), int(ui_value[2])


class PropertyUIHSVOpenCV(PropertyUIMultipleOpenCV):
    def __init__(self, window_name: str, prop: Property):
        super().__init__(window_name, prop)

    def prop_to_ui(self, prop_value):
        return [int(prop_value[0]), int(prop_value[1] * 255.0), int(prop_value[2] * 255.0)]

    def ui_to_prop(self, ui_value):
        return float(ui_value[0]), float(ui_value[1]) / 255.0, float(ui_value[2]) / 255.0


class PropertiesOpenCVUI(PropertiesListener):
    def __init__(self, properties_obj):
        self.properties = properties_obj
        self.properties.add_listener(self)
        self.properties_uis = dict()

    def close(self):
        cv2.destroyAllWindows()
        self.properties_uis = dict()

    def show(self, node_path: str):
        # todo: prevent double showing?
        node = self.properties.node_at_path(node_path)
        if isinstance(node, Properties):
            window_name = node_path
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # todo: better name in json?
            for prop in node.child_nodes():
                if prop.type != PropNodeType.group:
                    self.track_ui_for_property(self.create_ui_for_property(prop, window_name))
                else:
                    print("Cannot show SUB groups in OPEN_CV...")

        self.sync_ui_to_prop(node_path)

    def on_prop_updated(self, prop: PropertyNode, from_runtime_change: bool = True):
        """
        Called when a property value is changed - implements PropertiesListener
        :param prop:
        :param from_runtime_change:
        :return:
        """
        self.sync_ui_to_prop(prop.path_as_str())

    @staticmethod
    def create_ui_for_property(prop: Property, window_name) -> PropertyUIOpenCV:
        if prop.type == PropNodeType.rgb:
            return PropertyUIRGBOpenCV(window_name, prop)
        elif prop.type == PropNodeType.hsv:
            return PropertyUIHSVOpenCV(window_name, prop)
        else:
            return PropertyUIOpenCV(window_name, prop)

    def track_ui_for_property(self, ui: PropertyUIOpenCV):
        # keep track of UI elements...
        path = ui.prop.path_as_str()
        if path not in self.properties_uis:
            self.properties_uis[path] = []
        self.properties_uis[path].append(ui)

    def get_uis_for_property(self, prop: Property) -> Optional[List[PropertyUIOpenCV]]:
        path = prop.path_as_str()
        if path in self.properties_uis:
            return self.properties_uis[path]
        return None

    def sync_ui_to_prop(self, node_path: str):
        node = self.properties.node_at_path(node_path)
        if node.type == PropNodeType.group:
            for sub_node in node.child_nodes():
                self.sync_ui_to_prop(sub_node.path_as_str())
        else:
            uis_for_node = self.get_uis_for_property(node)
            if uis_for_node is not None:
                for ui in uis_for_node:
                    ui.sync_ui_to_prop()
