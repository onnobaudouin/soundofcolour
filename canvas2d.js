class Canvas2D {
    constructor(dom_id = null) {
        this.ctx = null;
        if (dom_id !== null) {
            let element = document.getElementById(dom_id);
            if (element !== null) {
                if (element.nodeName.toLowerCase() === 'canvas') {
                    this.connect_to_canvas(element);
                }
            }
        }
    }
    
    connect_to_canvas(canvas_element) {
        this.canvas = canvas_element;
        this.ctx = this.canvas.getContext("2d");
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
    
    update_resolution(width, height) {
        if (
            (width !== this.canvas.width) ||
            (height !== this.canvas.height)) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
    }
    
    
}