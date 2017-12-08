from enum import Enum
import sys
from jsonfile import JSONFile
from pprint import pprint
import collections
from typing import Optional, Union, Any, List, Dict


class PropNodeType(Enum):
    group = 0
    unsigned_int = 1
    int = 2
    unsigned_float = 3
    bool = 4
    rgb = 5
    hsv = 6
    string = 7
    float = 8


# TODO: cleanup the type system with classes...
# class PropInt:
#     @staticmethod
#     def range():
#         return -sys.maxsize, sys.maxsize
#
#     @staticmethod
#     def default():
#         return 0
#
#
# class PropUnsignedInt(PropInt):
#     @staticmethod
#     def range():
#         return 0, sys.maxsize
#
#
# class PropFloat:
#     @staticmethod
#     def range():
#         return float("-inf"), float("inf")
#
#     @staticmethod
#     def default():
#         return 0.0
#
#
# class PropUnsignedFloat(PropFloat):
#     @staticmethod
#     def range():
#         mi, ma = super(PropUnsignedFloat, PropUnsignedFloat).range()
#         return 0, ma
#
#
# class PropBool:
#     @staticmethod
#     def range():
#         return False, True
#
#     @staticmethod
#     def default():
#         return False
#
#
# class PropColour:
#     @staticmethod
#     def range():
#         return (0, 0, 0), (255, 255, 255)
#
#     @staticmethod
#     def default():
#         return 0, 0, 0
#
#
# class PropRGB(PropColour):
#     pass
#
#
# class PropHSV(PropColour):
#     @staticmethod
#     def range():
#         return (0, 0, 0), (180, 255, 255)
class PropertyNode:
    def __init__(self, name, type):
        self.type = type
        self.name = name

    def as_description(self) -> collections.OrderedDict:
        return collections.OrderedDict(
            [("name", self.name),
             ("type", PropNodeType(self.type).name.lower())
             ])

    def as_dict(self) -> Dict:
        return {
            self.name: self.contents()
        }

    def contents(self):
        return None


class Property(PropertyNode):
    numerics = [PropNodeType.unsigned_int,
                PropNodeType.int,
                PropNodeType.float,
                PropNodeType.unsigned_float]

    numeric_tuple = [PropNodeType.rgb, PropNodeType.hsv]

    def __init__(self, name, type, default=None, value=None):
        super().__init__(name, type)
        self.default = default
        self.min = None
        self.max = None
        self._value = None
        self.names = []
        self.dirty = False

        if self.type == PropNodeType.unsigned_int:
            self.min = 0
            self.max = sys.maxsize
        elif self.type == PropNodeType.int:
            self.min = -sys.maxsize
            self.max = sys.maxsize
        elif self.type == PropNodeType.float:
            self.min = float("-inf")
            self.max = float("inf")
        elif self.type == PropNodeType.unsigned_float:
            self.min = 0.0
            self.max = float("inf")
        elif self.type == PropNodeType.bool:
            self.min = 0
            self.max = 1
        elif self.type == PropNodeType.rgb:
            self.min = (0, 0, 0)
            self.max = (255, 255, 255)
            self.names = ["red", "green", "blue"]
        elif self.type == PropNodeType.hsv:
            self.min = (0, 0, 0)
            self.max = (180, 255, 255)
            self.names = ["hue", "saturation", "luminosity"]
        if self.default is None:
            if self.is_single_numeric():
                self.default = 0
            if self.type == PropNodeType.bool:
                self.default = False
            if self.type in self.numeric_tuple:
                self.default = (0, 0, 0)

        if value is not None:
            self.set(value)
        else:
            self.set(self.default)

    def as_description(self):
        d = super().as_description()
        d["min"] = self.min
        d["max"] = self.max
        d["default"] = self.default
        d["names"] = self.names
        return d

    def range(self, minimum=None, maximum=None):
        if minimum is not None:
            self.min = minimum
        if maximum is not None:
            self.max = maximum
        return self.min, self.max

    def is_single_numeric(self):
        return self.type in Property.numerics

    @staticmethod
    def clip(val, mi, ma):
        if val < mi:
            return mi
        if val > ma:
            return ma
        return val

    # returns True if value was changed
    def set(self, value, index=None, from_runtime_change: bool=False):
        temp_value = self.value()
        if self.is_single_numeric():
            self._value = self.clip(value, self.min, self.max)
        if self.type in Property.numeric_tuple:
            if (index is not None) and (index < len(self.min)):
                t = list(self._value)
                t[index] = self.clip(value, self.min[index], self.max[index])
                self._value = tuple(t)
            elif len(value) == len(self.min):
                p = []
                # surely there is a more python way...
                for v, mi, ma in zip(value, self.min, self.max):
                    p.append(self.clip(v, mi, ma))
                self._value = tuple(p)

        if self.type == PropNodeType.bool:
            if value == 0 or value is False:
                self._value = False
            elif value == 1 or value is True:
                self._value = True
            else:
                self._value = self.default

        was_changed = temp_value != self.value()
        if from_runtime_change:
            self.dirty = was_changed or self.dirty

        return was_changed

    def value(self):
        return self._value

    def clean(self):
        self.dirty = False

    def is_dirty(self):
        return self.dirty

    def from_contents(self, contents):
        if (self.is_single_numeric() or
                (self.type == PropNodeType.bool) or
                (self.type == PropNodeType.string)):
            self.set(contents)
        elif self.type in Property.numeric_tuple:
            self.set(tuple(contents))

    def contents(self):
        if (self.is_single_numeric() or
                (self.type == PropNodeType.bool) or
                (self.type == PropNodeType.string)):
            return self.value()
        elif self.type in Property.numeric_tuple:
            return list(self.value())
        pass


class Properties(PropertyNode):
    def __init__(self, name: str, window_name=None):
        super().__init__(name, PropNodeType.group)
        self.children = collections.OrderedDict()  # Ordered because adding is hierarchical
        self.path = None
        # self.dirty = False
        self.window_name = self.name

    def child_nodes(self) -> List[Union[PropertyNode, Property, "Properties"]]:
        return [x for key, x in self.children.items()]

    def add_group(self, name: str) -> "Properties":
        """Add a group node that will contain subnodes, but is itself contains no data

        :param name:
        :return: Property
        """
        return self.add(name, PropNodeType.group)

    def add(self, name: str, prop_type: PropNodeType, default=None, minimum=None, maximum=None):
        if prop_type is PropNodeType.group:
            p = Properties(name)
        else:
            p = Property(name, prop_type, default, default)
            p.range(minimum, maximum)

        self.children[name] = p
        return p

    def contents(self) -> collections.OrderedDict:
        """Returns the contents, i.e. structure AND data of this node and subnodes.
        It does NOT return a named-root. i.e. the calling nodes name is not included. use
        from_dict() instead.

        :return: OrderedDict
        """
        d = collections.OrderedDict()
        for node in self.child_nodes():
            d[node.name] = node.contents()
        return d

    def from_contents(self, contents: collections.OrderedDict):
        for node in self.child_nodes():
            if node.name in contents:
                node.from_contents(contents[node.name])

    def from_dict(self, dictionary: dict):
        self.from_contents(dictionary[self.name])

    def save(self, path, file_type="json"):
        if file_type == "json":
            d = self.contents()
            JSONFile.save(path, d)
        pass

    def is_dirty(self) -> bool:
        for node in self.child_nodes():
            if node.is_dirty():
                return True
        return False

    def clean(self):
        for node in self.child_nodes():
            node.clean()

    def update_permanent_storage(self):
        if self.path is not None and self.is_dirty():
            self.save(self.path)
            self.clean()

    def load(self, path: str, file_type="json"):
        if file_type == "json":
            data = JSONFile.load(path)
            self.path = path
            if data is not None:
                self.from_contents(data)
                print("loaded: " + self.path)
            else:
                self.from_contents(self.contents())
                print("loaded from defaults")
        pass

    def node_path_list_of(self, node_path: Union[List[str], str]) -> List[str]:
        """From varied input return a list of nodenames in order of hierarchy.

        """
        if isinstance(node_path, str):
            return node_path.split('/')
        return node_path

    def node_at_path(self, node_path: Union[List[str], str]) -> Optional[PropertyNode]:
        node_path_list = self.node_path_list_of(node_path)
        current_node = self
        for node_name in node_path_list:
            current_node = current_node.named_node(node_name)
            if current_node is None:
                print("Node not found: " + "/".join(node_path_list))
                return None
            if current_node.type != PropNodeType.group:  # actual data node (i.e. LEAF) so return as CANNOT continue.
                return current_node
            else:
                pass  # i.e. go one deeper in hierarchy.
        return current_node

    def named_node(self, node_name: str) -> Optional[PropertyNode]:
        if node_name in self.children:
            return self.children[node_name]
        return None

    def property_at_path(self, node_path) -> Optional[Property]:
        node = self.node_at_path(node_path)
        if node is not None:
            if isinstance(node, Property):
                return node
            else:
                print("Valid nodepath but a group node not a property")
        return None

    def group_at_path(self, node_path) -> Optional["Properties"]:
        # https://blog.jetbrains.com/pycharm/2015/11/python-3-5-type-hinting-in-pycharm-5/
        node = self.node_at_path(node_path)
        if node is not None:
            if isinstance(node, Properties):
                return node
            else:
                print("Valid nodepath but a property not a group")
        return None

    def value_of(self, node_path: Union[List[str], str]) -> Any:
        node = self.property_at_path(node_path)
        if node is not None:
            return node.value()

    def set_value_of(self, node_path: Union[List[str], str], value: Any, from_run_time: bool = False) -> Any:
        node = self.property_at_path(node_path)
        if node is not None:
            return node.set(value=value, from_runtime_change=from_run_time)

    def as_description(self) -> collections.OrderedDict:
        """Returns a complete description of all propeties and hierarchy but NO DATA.

        :return:
        """
        prop_descriptions = [p.as_description() for key, p in self.children.items()]
        d = super().as_description()
        d["children"] = prop_descriptions
        return d


if __name__ == "__main__":
    props = Properties('test')
    ui = props.add_group("ui")
    ui.add("blur", PropNodeType.unsigned_int, maximum=250)
    ui.add("min_circle", PropNodeType.unsigned_int, maximum=250)
    ui.add("max_circle", PropNodeType.unsigned_int, maximum=250, default=10)
    ui.add("show_masks", PropNodeType.bool, default=True)
    ui.add("min_area", PropNodeType.unsigned_int)
    colours = props.add_group("colours")
    col = ["blue", "green", "yellow", "orange", "pink"]
    for name in col:
        colour = colours.add_group(name)
        colour.add('min_hsv', PropNodeType.hsv)
        colour.add('max_hsv', PropNodeType.hsv)
    import json

    contents = props.contents()
    pprint(contents)
    json_contents = json.dumps(contents, indent=2)
    print(json_contents)

    unjson_contents = json.loads(json_contents)
    props.from_contents(unjson_contents)
    pprint(contents)
    props.save('test.json')
    props.load('test.json')
    pprint(contents)

    pprint(props.value_of("ui/max_circle"))
    props.set_value_of('ui/max_circle', 50)
    pprint(props.value_of("ui/max_circle"))
    props.set_value_of('ui/max_circle', 450)
    pprint(props.value_of("ui/max_circle"))

    # print(json.dumps(props.as_dict(), indent=2))

    # pprint(props.as_description())
    # import json
    # print(json.dumps(props.as_description(), indent=2))
    # props.load('test.json')
    # pprint(props.as_dict())
    # props.save('test.json')
