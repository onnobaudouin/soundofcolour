class Canvas2D {
    constructor(dom_id = null) {
        this.ctx = null;
        if (dom_id !== null) {
            let element = document.getElementById(dom_id);
            if (element !== null) {
                if (element.nodeName.toLowerCase() === 'canvas') {
                    this.connect_to_canvas(element);
                    this.connect_mouse();
                    
                }
            }
        }
        this.mouse_event_handler = null;
    }
    
    connect_to_canvas(canvas_element) {
        this.canvas = canvas_element;
        this.ctx = this.canvas.getContext("2d");
    }
    
    connect_mouse() {
        this.canvas.addEventListener('mousemove', evt => {
                const mousePos = this.getMousePos(evt);
                if(this.mouse_event_handler) {
                    this.mouse_event_handler('move', mousePos)
                }
            }
        );
        this.canvas.addEventListener('mouseup', evt => {
                const mousePos = this.getMousePos(evt);
                if(this.mouse_event_handler) {
                    this.mouse_event_handler('up', mousePos)
                }
            }
        );
        this.canvas.addEventListener('mousedown', evt => {
                const mousePos = this.getMousePos(evt);
                if(this.mouse_event_handler) {
                    this.mouse_event_handler('down', mousePos)
                }
            }
        );
    }
    
    getMousePos(evt) {
        const rect = this.canvas.getBoundingClientRect();
        const x1 = evt.clientX - rect.left;
        const y1 = evt.clientY - rect.top;
        return {
            x: x1,
            y: y1,
            xPercent: x1 / rect.width,
            yPercent: y1 / rect.height,
            width: rect.width,
            height: rect.height
        };
    }

    
   
    
    ready() {
        return (this.ctx !== null);
    }
    
    clear() {
        if (!this.ready()) return; //todo implement as empty functions?
        this.ctx.fillStyle = "black";
        //ctx.fillRect(0,0,300,150);
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
    }
    
    width() {
        return this.canvas.width
    }
    
    height() {
        return this.canvas.height
    }
    image(image) {
        if (!this.ready()) return; //todo implement as empty functions?
        this.ctx.drawImage(image, 0, 0);
    }
    
    disc(x, y, radius, colour) {
        if (!this.ready()) return; //todo implement as empty functions?
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
        this.ctx.fillStyle = colour;
        this.ctx.fill();
    }
    
    circle(x, y, radius, colour) {
        if (!this.ready()) return; //todo implement as empty functions?
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
        this.ctx.strokeStyle = colour;
        this.ctx.stroke();
    }
    
    update_resolution(width, height) {
        if (
            (width !== this.canvas.width) ||
            (height !== this.canvas.height)) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
    }
    
    line(x,y, x_to, y_to, colour) {
        if (!this.ready()) return; //todo implement as empty functions?
        this.ctx.beginPath();
       // console.log(colour);
        this.ctx.strokeStyle = 'rgb('+colour.join(',')+')';
        this.ctx.moveTo(x,y);
        this.ctx.lineTo(x_to,y_to);
        this.ctx.stroke();
    
    }
    
    
}