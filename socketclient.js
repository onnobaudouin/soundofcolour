class SocketClient {
    constructor(url = null) {
        this.url = url;  //e.g. "ws://localhost:8001/"
        this.websocket = null;
        this.auto_reconnect = true;
        this.auto_reconnect_interval_id = null;
        this.openHandler = evt => this.on_open_private(evt);
        this.closeHandler = evt => this.on_close_private(evt);
        this.messageHandler = evt => this.on_message(evt);
        this.errorHandler = evt => this.on_error_private(evt);
    }
    
    on_open_private(event) {
        console.log('connection open');
        this.on_open(event);
        
    }
    
    on_open(event) {
    
    }
    
    on_close_private(close_event) {
        console.log('connection closed: ' + close_event.code + ' ' + close_event.reason);
        this.update_auto_reconnect();
        this.on_close(close_event);
    }
    
    on_close(close_event) {
    
    }
    
    on_message(message_event) {
        console.log('message received. size:' + message_event.data.length);
    }
    
    on_error_private(error_event) {
        this.update_auto_reconnect();
        this.on_error(error_event);
    }
    
    on_error(event) {
        console.log('connection error: ' + event.type);
    }
    
    is_connected() {
        if (this.websocket !== null) {
            return (this.websocket.readyState === this.websocket.OPEN);
        }
    }
    
    disconnected() {
        this.disconnect_handlers();
        console.log("closing...");
        this.websocket.close();
        this.websocket = null;
    }
    
    close() {
        if (this.is_connected()) {
            this.disconnected();
        }
    }
    
    update_auto_reconnect() {
        this.disconnected();
        if (this.auto_reconnect) {
            console.log('will attempt reconnect in 1 second');
            this.auto_reconnect_interval_id = setInterval(() => this.start_connect(), 1000)
        }
    }
    
    stop_auto_reconnect() {
        clearInterval(this.auto_reconnect_interval_id);
        this.auto_reconnect_interval_id = null;
    }
    
    connect_handlers() {
        let ws  = this.websocket;
        ws.addEventListener('open', this.openHandler);
        ws.addEventListener('close', this.closeHandler);
        ws.addEventListener('message', this.messageHandler);
        ws.addEventListener('error', this.errorHandler);
    }
    
    disconnect_handlers() {
        let ws  = this.websocket;
        ws.removeEventListener('open', this.openHandler);
        ws.removeEventListener('close', this.closeHandler);
        ws.removeEventListener('message', this.messageHandler);
        ws.removeEventListener('error', this.errorHandler);
    }
    
    send_raw(message) {
        if (this.is_connected()) {
            this.websocket.send(message); //todo: probably has some errors it can throw
        }
    }
    
    send_json(message) {
        this.send_raw(JSON.stringify(message));
    }
    
    start_connect() {
        if (this.is_connected()) {
            this.close();
        }
        console.log("Connecting...");
        this.stop_auto_reconnect();
        try {
            this.websocket = new WebSocket(this.url);
        } catch (ex) {
            console.log(ex + ' port probably closed');
            this.websocket = null;
            return;
        }
        this.connect_handlers();
    }
}