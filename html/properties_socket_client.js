class PropertiesSocketClient extends SocketClient {
    constructor(do_ui=true) {
        super();
        this.do_ui = do_ui;
        this.properties_ui = null;
        this.properties = null;
        this.task_id = 0;
        this.debug_level = 2;
    }
    
    on_close(event) {
        console.log("connection closed - killing ui...");
        if (this.do_ui) {
            this.properties_ui.destroy();
            this.properties_ui = null;
        }
        
    }
    
    on_open(event) {
        console.log("connected....");
    }
    
    
    //https://developer.mozilla.org/en-US/docs/Web/API/MessageEvent
    on_message(message_event) {
        const message_raw = message_event.data;
        let message = null;
        try {
            message = JSON.parse(message_raw);
            if (this.debug_level === 3) {
                console.log('received: ');
                console.log(message);
            }
        }
        catch (ex) {
            console.log(ex);
            console.log(message_raw);
            return;
        }
        if ("type" in message) {
            switch (message.type) {
                case 'welcome':
                    this.on_message_welcome();
                    break;
                case 'prop_description':
                    this.on_message_prop_description(message['data']);
                    break;
                case 'prop_all':
                    this.on_message_prop_all(message['data']);
                    break;
                case 'prop':
                    this.on_message_prop(message['data']);
                    break;
                case 'tasks_per_frame':
                    this.on_message_tasks_per_frame(message['data']);
                    break;
            }
        } else {
            console.log('unknown message :' + message_raw);
        }
    }
    
    on_message_welcome() {
        console.log("Server said welcome...");
        this.send_message('prop_description')
    }
    
    on_message_prop_description(message) {
        let t = Properties.create_from_description_object(message);
        
        this.dynamic_method_call("on_add_custom_props", [t]);
        if (this.do_ui) {
            this.properties_ui = new DatGUIPropertiesView();
            this.properties_ui.from_properties(t);
        }
        
        this.properties = t;
        
        this.send_message('prop_all'); //todo -> request all
    }
    
    on_message_prop_all(message) {
        console.log(message);
        this.properties.from_contents(message);
        if (this.do_ui) {
            this.properties_ui.update();
            this.properties_ui.onChanged = (prop_node) => {
                this.onPropChanged(prop_node);
            };
        }
        this.dynamic_method_call("on_properties_loaded", []);
    }
    
    on_message_tasks_per_frame(message) {
        message.tasks.forEach(task => {
            this.dynamic_method_call("on_task_" + task.task, [task.result]); //todo rename task.task -> task.name
        });
    }
    
    on_message_prop(message) {
        console.log(message);
        this.properties.set_value_of(message.path, message.value);
        if (this.do_ui) {
            this.properties_ui.update();
        }
    }
    
    send_property_update(path, value) {
        this.send_message('prop', {'path': path, 'value': value});
    }
    
    send_message(type, message = {}) {
        message.type = type;
        if (this.debug_level === 3) {
            console.log('sending :');
            console.log(message);
        }
        this.send_json(message);
    }
    
    
    send_tasks_per_frame(task, id = null, state = null, data = null) {
        task = this.get_task(task, id, state, data);
        this.send_message("tasks_per_frame",
            {
                'tasks': [
                    task
                ]
            });
        return task;
    }
    
    get_task(task, id = null, state = null, data = null) {
        if (id === null) {
            id = 't_' + this.task_id++;
        }
        return {
            "task": task,
            "state": state,
            "id": id,
            "data": data
        }
    }
    
    onPropChanged(prop_node) {
        const path = prop_node.path_as_string();
        const handled = this.dynamic_method_call("on_handle_property_changed", [path, prop_node]);
        if (handled === false) {
            this.send_property_update(path, prop_node.value())
        }
    }
    
    
    dynamic_method_call(methodName, args) {
        if (methodName in this) {
            return this[methodName].apply(this, args)
        }
        return undefined;
    }
}
