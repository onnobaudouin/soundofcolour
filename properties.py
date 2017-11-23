from enum import Enum
import sys
from JSON import JSON
from pprint import pprint
import collections


class PropType(Enum):
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


class Property:
    numerics = [PropType.unsigned_int,
                PropType.int,
                PropType.float,
                PropType.unsigned_float]

    numeric_tuple = [PropType.rgb, PropType.hsv]

    def __init__(self, name, type, default=None, value=None):
        self.type = type
        self.default = default
        self.min = None
        self.max = None
        self._value = None
        self.name = name

        if self.type == PropType.unsigned_int:
            self.min = 0
            self.max = sys.maxsize
        elif self.type == PropType.int:
            self.min = -sys.maxsize
            self.max = sys.maxsize
        elif self.type == PropType.float:
            self.min = float("-inf")
            self.max = float("inf")
        elif self.type == PropType.unsigned_float:
            self.min = 0.0
            self.max = float("inf")
        elif self.type == PropType.bool:
            self.min = 0
            self.max = 1
        elif self.type == PropType.rgb:
            self.min = (0, 0, 0)
            self.max = (255, 255, 255)
        elif self.type == PropType.hsv:
            self.min = (0, 0, 0)
            self.max = (180, 255, 255)

        if self.default is None:
            if self.is_single_numeric():
                self.default = 0
            if self.type == PropType.bool:
                self.default = False
            if self.type in self.numeric_tuple:
                self.default = (0, 0, 0)

        if value is not None:
            self.set(value)
        else:
            self.set(self.default)

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

    def set(self, value):
        if self.is_single_numeric():
            self._value = self.clip(value, self.min, self.max)
        if self.type in Property.numeric_tuple:
            if len(value) == len(self.min):
                p = []
                # surely there is a more python way...
                for v, mi, ma in zip(value, self.min, self.max):
                    p.append(self.clip(v, mi, ma))
                self._value = tuple(p)
        if self.type == PropType.bool:
            if value == 0 or value is False:
                self._value = False
            elif value == 1 or value is True:
                self._value = True
            else:
                self._value = self.default

    def value(self):
        return self._value

    def from_dict(self, dictionary):
        if (self.is_single_numeric() or
                (self.type == PropType.bool) or
                (self.type == PropType.string)):
            self.set(dictionary[self.name])
        elif self.type in Property.numeric_tuple:
            self.set(tuple(dictionary[self.name]))

    def as_dict(self):
        if (self.is_single_numeric() or
                (self.type == PropType.bool) or
                (self.type == PropType.string)):
            return {
                self.name: self.value()
            }
        elif self.type in Property.numeric_tuple:
            return {
                self.name: list(self.value())
            }

        pass


class Properties:
    def __init__(self, name=None):
        self.props = collections.OrderedDict()
        self.groups = collections.OrderedDict()
        self.name = name

    def group(self, name):
        p = Properties(name)
        self.groups[name] = p
        return p

    def add(self, name, prop_type, default=None, minimum=None, maximum=None):
        p = Property(name, prop_type, default, default)
        p.range(minimum, maximum)
        self.props[name] = p

    def as_dict(self):
        d = collections.OrderedDict()
        for key, p in self.props.items():
            d[p.name] = p.as_dict()[p.name]
        for key, g in self.groups.items():
            d[g.name] = g.as_dict()
        return d

    def from_dict(self, data):
        for key, g in self.groups.items():
            if g.name in data:
                g.from_dict(data[g.name])

        for key, p in self.props.items():
            if p.name in data:
                p.from_dict({p.name: data[p.name]})

    def save(self, path, file_type="json"):
        if file_type == "json":
            d = self.as_dict()
            JSON.save(path, d)
        pass

    def load(self, path, file_type="json"):
        if file_type == "json":
            data = JSON.load(path)
            if data is not None:
                self.from_dict(data)

        pass

    def set(self, name, value):
        if name in self.props:
            self.props[name].set(value)
        else:
            print("No Such property: " + name)

    def node_from_path(self, node_path):
        if isinstance(node_path, str):
            node_path = node_path.split('/')
        node = self
        for node_name in node_path:
            node = node.node(node_name)
            if node is None:
                return None
            if isinstance(node, Property):
                return node
            # node should be a properties so continue
        return node

    def node(self, node_name):
        if node_name in self.props:
            return self.props[node_name]
        if node_name in self.groups:
            return self.groups[node_name]
        return None






if __name__ == "__main__":
    props = Properties()
    ui = props.group("ui")
    ui.add("blur", PropType.unsigned_int, maximum=250)
    ui.add("min_circle", PropType.unsigned_int, maximum=250)
    ui.add("max_circle", PropType.unsigned_int, maximum=250)
    ui.add("show_masks", PropType.bool)
    ui.add("min_area", PropType.unsigned_int)
    colours = props.group("colours")
    col = ["blue", "green", "yellow", "orange", "pink"]
    for name in col:
        colour = colours.group(name)
        colour.add('min_hsv', PropType.hsv)
        colour.add('max_hsv', PropType.hsv)
    # pprint(props.as_dict())
    props.load('pi.json')
    # pprint(props.as_dict())
    props.save('pi.json')
