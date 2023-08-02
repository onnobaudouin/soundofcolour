class DatGUIPropertiesView {
    constructor() {
        this.properties = null;
    }
    
    from_properties(properties) {
        this.properties = properties;
        this.gui_obj = {};
        this.gui = new dat.GUI();
        this.add_from_propnode(this.properties, this.gui, this.gui_obj);
        this.onChanged = null;
        
    }
    
    destroy() {
        this.properties = null;
        if (typeof this.gui !== "undefined") {
            this.gui.destroy();
        }
        this.gui_obj = null;
        this.onChanged = null;
    }
    
    attach_event_handler(prop_node, dat_object, sub='', sub_index=-1) {
        if (sub_index === -1) {
            prop_node.dat_controller = dat_object;
            prop_node.dat_controller.onChange((value) => {
                this.onChange(prop_node, value)
            });
        } else {
            //one propnode has multiple DAT_GUI controllers - keep track of all...
            if (typeof prop_node.dat_controllers === 'undefined') {
                prop_node.dat_controllers = {}
            }
            prop_node.dat_controllers[sub] = dat_object
            prop_node.dat_controllers[sub].onChange((value) => {
                this.onChange(prop_node, value, sub, sub_index)
            });
        }
    }
    
    update() {
        this.update_node(this.properties);
    }
    
    //PROP to UI
    update_node(prop_node) {
        let path = prop_node.path().join('/');
        switch(prop_node.type) {
            case PropNodeType.group: {
                prop_node.child_nodes().forEach(prop_node => {this.update_node(prop_node)});
            } break;
            case PropNodeType.unsigned_int:
            case PropNodeType.unsigned_float:
            case PropNodeType.float:
            case PropNodeType.int:
            case PropNodeType.bool:
            case PropNodeType.rgb:
            case PropNodeType.string:
            {
                this.gui_obj[path] = prop_node.value(); //the way DAT works
                prop_node.dat_controller.updateDisplay(); //update ui.
            } break;
            case PropNodeType.hsv:
            {
                let t = prop_node.value();
                this.gui_obj[path] = {h:parseInt(t[0]), s:t[1], v:t[2]};
                prop_node.dat_controller.updateDisplay(); //update ui.
            } break;
            case PropNodeType.point:
            case PropNodeType.rect:
            {
                let t = prop_node.value();
                prop_node.names.forEach((name, index) => {
                    let subpath = path+':'+name;
                    this.gui_obj[subpath] = t[index];
                   // this.attach_event_handler(prop_node, f.add(gui_obj, subpath).min(prop_node.min[index]+0.0).max(prop_node.max[index]+0.0), name, index);
                    prop_node.dat_controllers[name].updateDisplay(); //update ui.
        
                });
               
                
                
                
            }   break;
        }
    }
    
    trigger_notification(proppath) {
        let prop_node = this.properties.node_at_path(proppath);
        this.notify(prop_node);
    }
    
    //UI to PROP
    onChange(prop_node, value, sub='', sub_index=0) {
       // console.log(prop_node.path().join('/') +sub+ ' = '+value);
        switch (prop_node.type) {
            case PropNodeType.unsigned_int:
            case PropNodeType.unsigned_float:
            case PropNodeType.float:
            case PropNodeType.int:
            case PropNodeType.bool:
            case PropNodeType.string:
            {
                if(prop_node.set(value, undefined, true)) {
                    //todo - properties should notify!
                    this.notify(prop_node);
                }
                
            } break;
            case PropNodeType.hsv:
            {
                if(prop_node.set([parseInt(value.h), value.s, value.v], undefined, true)) {
                    this.notify(prop_node);
                }
            } break;
            case PropNodeType.rgb:
            {
               // console.log('rgb: '+value);
                if(prop_node.set(value.map(x=> Math.round(x)) , undefined, true)) {
                    //todo - properties should notify!
                    this.notify(prop_node);
                }
            } break;
    
            case PropNodeType.point:
            case PropNodeType.rect:
            {
                if(prop_node.set(value, sub_index)) {
                    //todo - properties should notify!
                    //console.log('notifiy point or rect'+value+' / '+sub_index);
                    this.notify(prop_node);
                }
            } break;
            
        }
    }
    
    notify(prop_node) {
        if (this.onChanged !== null) {
            this.onChanged(prop_node);
        }
    }
    
    add_from_propnode(prop_node, gui, gui_obj, folder=null) {
        let path = prop_node.path().join('/');
        let prop_attach = gui;
        if (folder !== null) {
            prop_attach = folder;
        }
        switch (prop_node.type) {
            case PropNodeType.group: {
                let f = null;
                if (prop_node.parent !== null) {
                    f = gui.addFolder(path); //TODO add sub folder..
                }
                prop_node.child_nodes().forEach(node => this.add_from_propnode(node, gui, gui_obj, f));
                break;
            }
            case PropNodeType.unsigned_int: {
                gui_obj[path] = prop_node.default;
                this.attach_event_handler(prop_node, prop_attach.add(gui_obj, path).step(1).min(prop_node.min).max(prop_node.max));
                
                break;
            }
            case PropNodeType.unsigned_float:
            case PropNodeType.float: {
                gui_obj[path] = prop_node.default;
                this.attach_event_handler(prop_node, prop_attach.add(gui_obj, path).min(prop_node.min).max(prop_node.max));
        
                break;
            }
            case PropNodeType.bool: {
                gui_obj[path] = prop_node.default;
                this.attach_event_handler(prop_node, prop_attach.add(gui_obj, path));
                break;
            }
            case PropNodeType.hsv: {
                let t = prop_node.default;
                gui_obj[path] ={h:t[0], s:t[1], v:t[2]};
                this.attach_event_handler(prop_node, prop_attach.addColor(gui_obj, path));
                
                break;
            }
            case PropNodeType.rgb: {
                gui_obj[path] = prop_node.default;
                this.attach_event_handler(prop_node,prop_attach.addColor(gui_obj, path));
                break;
            }
            case PropNodeType.rect:
            case PropNodeType.point: {
                let f = gui.addFolder(path);
                prop_node.names.forEach((name, index) => {
                    let subpath = path+':'+name;
                    gui_obj[subpath] = prop_node.default[index];
                    this.attach_event_handler(prop_node, f.add(gui_obj, subpath).min(prop_node.min[index]+0.0).max(prop_node.max[index]+0.0).step(0.001), name, index);
                    
                });
                break;
            }
            default: {
                console.log('cannot handle: '+prop_node.type);
            }
            
        }
    }
    
}