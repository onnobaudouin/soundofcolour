const PropNodeType = {
    group: 0,
    unsigned_int: 1,
    int: 2,
    unsigned_float: 3,
    bool: 4,
    rgb: 5,
    hsv: 6,
    string: 7,
    float: 8
};

const PropTypeSingleNumeric = [
    PropNodeType.unsigned_int,
    PropNodeType.int,
    PropNodeType.float,
    PropNodeType.unsigned_float
];

const PropTypeMultipleNumeric = [
    PropNodeType.rgb,
    PropNodeType.hsv,
];

class PropNode {
    constructor(name, type, parent = null) {
        this.name = name;
        this.type = type;
        /**
         * @var PropNode
         */
        this.parent = parent;
    }
    
    contents() {
        return null;
    }
    
    as_description() {
        let description = new Map();
        description.set("name", this.name);
        description.set("type", this.key_from_value(PropNodeType, this.type));
        return description;
    }
    
    key_from_value(object, value) {
        // https://stackoverflow.com/questions/36448649/get-key-corresponding-to-value-in-js-object
        return Object.keys(object).find(key => object[key] === value);
    }
    
    as_dict() {
        let d = {};
        d[this.name] = this.contents()
    }
    
    path() {
        let p = [this.name];
        let node = this.parent;
        while (node !== null) {
            if (node.parent !== null) {
                p.push(node.name);
                node = node.parent;
            } else {
                node = null;
            }
        }
        return p.reverse();
    }
    
    
}

class Property extends PropNode {
    constructor(name, type, parent=null, _default = undefined, value = undefined) {
        super(name, type, parent);
        this.default = _default;
        this.min = undefined;
        this.max = undefined;
        this._value = undefined;
        this.names = [];
        this.dirty = false;
        
        switch (type) {
            case PropNodeType.unsigned_int:
                this.min = 0;
                this.max = Number.MAX_SAFE_INTEGER;
                break;
            case PropNodeType.int:
                this.min = Number.MIN_SAFE_INTEGER;
                this.max = Number.MAX_SAFE_INTEGER;
                break;
            case PropNodeType.float:
                this.min = Number.NEGATIVE_INFINITY;
                this.max = Number.POSITIVE_INFINITY;
                break;
            case PropNodeType.unsigned_float:
                this.min = 0.0;
                this.max = Number.POSITIVE_INFINITY;
                break;
            case PropNodeType.bool:
                this.min = 0;
                this.max = 1;
                break;
            case PropNodeType.rgb:
                this.min = [0, 0, 0];
                this.max = [255, 255, 255];
                this.names = ["red", "green", "blue"];
                break;
            case PropNodeType.hsv:
                this.min = [0, 0, 0];
                this.max = [180, 255, 255];
                this.names = ["hue", "saturation", "luminosity"];
                break;
            default:
                console.log("Unknown PropType: type")
        }
        if (this.default === undefined) {
            if (this.is_single_numeric()) {
                this.default = 0;
            } else if (this.type === PropNodeType.bool) {
                this.default = false;
            } else if (this.is_multiple_numeric()) {
                this.default = [0, 0, 0]; //todo: convert to float if float.?
            }
        }
        if (value !== undefined) {
            this.set(value);
        } else {
            this.set(this.default);
        }
        
    }
    
    is_single_numeric() {
        return PropTypeSingleNumeric.includes(this.type); //
    }
    
    is_multiple_numeric() {
        return PropTypeMultipleNumeric.includes(this.type);
    }
    
    range(minimum = undefined, maximum = undefined) {
        if (minimum !== undefined) {
            this.min = minimum;
        }
        if (maximum !== undefined) {
            this.max = maximum;
        }
        return [this.min, this.max];
    }
    
    static clip(val, mi, ma) {
        if (val < mi) {
            return mi;
        } else if (val > ma) {
            return ma;
        }
        return val;
    }
    
    set(value, index = undefined, from_run_time_change = false) {
        // TODO: check TYPES
        let temp_value = this.value();
        if (this.is_single_numeric()) {
            this._value = Property.clip(value, this.min, this.max);
        }
        else if (this.is_multiple_numeric()) {
            if ((index !== undefined) && (index < this.min.length)) {
                this._value[index] = Property.clip(value);
            } else if (value.length === this.min.length) {
                this._value = value.map((val, index) => {
                    return Property.clip(val, this.min[index], this.max[index]);
                });
            }
        }
        else if (this.type === PropNodeType.bool) {
            if ((value === true) || (value === 1)) {
                this._value = true;
            } else if ((value === false) || (value === 0)) {
                this._value = false;
            } else {
                console.log("bool not set coz not valid bool value: " + this.name);
            }
        }
        
        let was_changed = false;
        if (this.is_multiple_numeric()) {
            was_changed = !Property.are_numeric_arrays_the_same(temp_value, this._value);
        } else {
            was_changed = (temp_value !== this._value)
        }
        if (from_run_time_change) {
            this.dirty = was_changed || this.dirty;
        }
        return was_changed;
    }
    
    value() {
        return this._value;
    }
    
    static are_numeric_arrays_the_same(ar1, ar2) {
        if ((ar1 === undefined) || (ar1 === undefined)) {
            return false;
        }
        if (ar1.length !== ar2.length) {
            return false;
        }
        for (let index = 0; index < ar1.length; index++) {
            if (ar1[index] !== ar2[index]) {
                return false;
            }
        }
        return true;
    }
    
    as_description() {
        let d = super.as_description();
        d["min"] = this.min;
        d["max"] = this.max;
        d["default"] = this.default;
        d["names"] = this.names;
        return d;
    }
    
    clean() {
        this.dirty = false;
    }
    
    is_dirty() {
        return this.dirty;
    }
    
    from_contents(contents) {
        this.set(contents)
    }
    
    contents() {
        return this.value();
    }
    
    
}

class Properties extends PropNode {
    constructor(name, parent=null) {
        super(name, PropNodeType.group, parent);
        this.children = new Map();
    }
    
    child_nodes() {
        return this.children; //does MAP support iterate?
    }
    
    add_group(name) {
        return this.add(name, PropNodeType.group);
    }
    
    add(name, type, _default = undefined, minimum = undefined, maximum = undefined) {
        let p = null;
        if (type === PropNodeType.group) {
            p = new Properties(name, this)
        } else {
            p = new Property(name, type, this, _default);
            p.range(minimum, maximum);
        }
        this.children.set(name, p);
        return p;
    }
    
    contents() {
        let d = new Map();
        this.child_nodes().forEach(node => {
            d.set(node.name, node.contents());
        });
        return d;
    }
    
    contents_json() {
        return value_to_json(this.contents());
    }
    
    from_contents(contents) {
        this.child_nodes().forEach(node => {
            if (node.name in contents) { //Might need to be more robust. but should be POJO
                node.from_contents(contents[node.name]);
            }
        })
    }
    
    from_contents_json(contents_json) {
        let contents = JSON.parse(contents_json);
        this.from_contents(contents);
    }
    
    from_dict(dict) {
        this.from_contents(dict[this.name]);
    }
    
    save() {
        console.log('not implementd');
    }
    
    load() {
        console.log('not implementd');
    }
    
    is_dirty() {
        const nodes = this.child_nodes().values();
        for (let node of nodes) {
            if (node.is_dirty()) {
                return true;
            }
        }
        return false;
    }
    
    clean() {
        this.child_nodes().map(node => node.clean());
    }
    
    static node_path_list_of(node_path) {
        if (typeof node_path === 'string') {
            return node_path.split('/');
        }
        return node_path;
    }
    
    node_at_path(node_path) {
        const node_path_list = Properties.node_path_list_of(node_path);
        let current_node = this;
        for (let node_name of node_path_list) {
            current_node = current_node.named_node(node_name);
            if (current_node === null) {
                console.log("node not found: " + node_path_list.join('/'));
                return null;
            }
            if (current_node.type !== PropNodeType.group) {
                return current_node;
            }
        }
        return current_node;
    }
    
    named_node(name) {
        if (this.children.has(name)) {
            return this.children.get(name);
        }
        return null;
    }
    
    property_at_path(node_path) {
        const node = this.node_at_path(node_path);
        if (node !== null) {
            if (node.type !== PropNodeType.group) {
                return node;
            } else {
                console.log('Node found, but not a property');
            }
        }
        return null;
    }
    
    group_at_path(node_path) {
        const node = this.node_at_path(node_path);
        if (node !== null) {
            if (node.type === PropNodeType.group) {
                return node;
            } else {
                console.log('Node found, but not a group');
            }
        }
        return null;
    }
    
    value_of(node_path) {
        const node = this.property_at_path(node_path);
        if (node !== null) {
            return node.value();
        } else {
            console.log('node not found');
        }
    }
    
    set_value_of(node_path, value, from_run_time = false) {
        const node = this.property_at_path(node_path);
        if (node !== null) {
            return node.set(value, undefined, from_run_time); //indexed issue
        }
    }
    
    as_description() {
        let d = super.as_description();
        d.set('children', Array.from(this.child_nodes().values()).map(node => node.as_description()));
        return d;
    }
    
    as_description_json() {
        return value_to_json(this.as_description());
    }
    
    static create_from_description_object(description_obj, parent=null) {
        let type = PropNodeType[description_obj.type];
        if (type === PropNodeType.group) {
            let p = new Properties(description_obj.name, parent);
            description_obj.children.forEach(child => {
                p.children.set(child.name, Properties.create_from_description_object(child, p));
            });
            return p;
        } else {
            let p = new Property(description_obj.name, type, parent, description_obj.default);
            p.range(description_obj.min, description_obj.max);
            p.names = description_obj.names; //not sure (is this part of a type?)
            return p;
        }
    }
    
    
    /*let props = new Properties('test');
       let ui = props.add_group('ui');
       ui.add("blur", PropNodeType.unsigned_int);
       ui.add("min_circle", PropNodeType.unsigned_int);
       let colours = ["blue", "green", "yellow", "orange", "pink"];
       let col = props.add_group('colours');
       colours.forEach(colour_name => {
           let sub = col.add_group(colour_name);
           sub.add('min_hsv', PropNodeType.hsv);
           sub.add('max_hsv', PropNodeType.hsv);
       });
       console.log(props.contents());
       console.log(props.contents_json());
       console.log(props.as_description());
       console.log(props.as_description_json());*/
    
    
}