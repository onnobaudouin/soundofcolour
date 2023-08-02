function object_to_map(object) {
    let m = new Map();
    for (let key in object) {
        if (Object.prototype.hasOwnProperty.call(object, key)) {
            m.set(key, object[key]);
        }
    }
    return m;
}

function distance(x1, y1, x2, y2) {
    const dx = x1 - x2;
    const dy = y1 - y2;
    return Math.sqrt(dx * dx + dy * dy);
}

function hslToRgb(h, s, l) {
    let r, g, b;
    
    if (s === 0) {
        r = g = b = l; // achromatic
    } else {
        let hue2rgb = function hue2rgb(p, q, t) {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
            return p;
        };
        
        let q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        let p = 2 * l - q;
        r = hue2rgb(p, q, h + 1 / 3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1 / 3);
    }
    
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

//http://dev.theomader.com/gaussian-kernel-calculator/
function gaussian_kernel(size) {
    const kerns = [
        [1],
        null,
        [0.27901, 0.44198, 0.27901],
        null,
        [0.06136, 0.24477, 0.38774, 0.24477, 0.06136],
        null,
        [0.00598, 0.060626, 0.241843, 0.383103, 0.241843, 0.060626, 0.00598]
    ];
    //Q kerns[size].handle(out_of_bound:0)
    //  element(kerns, size, if out_of_bound)
    //size.is_between(1, 8)
    if (size >= 1 && size < 8) {
        return kerns[size - 1]; //0 indexede
    }
    return null;
}

function gaussian_blur(hist, size = 5, circular = true) {
    const kernel = gaussian_kernel(size);
    if (kernel === null) {
        console.log('Not A Valid Gaussian Kernel Size ' + size);
        return hist;
    }
    let index = 0;
    let kern_index = 0;
    const len = hist.length;
    let output = filled_array(len, 0);
    let offset = 0;
    const neg = Math.floor(size / 2.0);
    let value = 0;
    
    //1 D CONVOLVE
    for (; index < len; index++) { //FOR ALL ELEMENTS
        value = 0;
        for (kern_index = 0; kern_index < size; kern_index++) {
            offset = index + kern_index - neg;
            if (offset < 0) {
                if (circular) {
                    offset = len + offset; // - -
                } else {
                    offset = 0; //repeat keft most
                }
            } else if (offset >= len) {
                if (circular) {
                    offset = offset % len;
                } else {
                    offset = len - 1;
                }
            }
            value += (kernel[kern_index] * hist[offset]);
        }
        output[index] = value;
    }
    
    //console.log(output);
    return output;
}

function blur(hist, size = 5, circular = true, times = 1) {
    let output = hist;
    for (let i = 0; i < times; i++) {
        output = gaussian_blur(output, size, circular);
    }
    return output;
}


function findLocalMaxima(hist, window_size = 5, is_circular = true) {
    if (window_size % 2 === 0) {
        console.log("window_size must be uneven. findLocalMaxima");
        return null;
    }
    const len = hist.length;
    const output = [];
    let index = 0;
    let current_value = 0;
    const either_side = Math.floor(window_size / 2.0);
    let window_index = 0;
    let is_highest = false;
    for (; index < len; index++) { //FOR ALL ELEMENTS
        current_value = hist[index];
        is_highest = true;
        for (window_index = index - either_side; window_index < index + either_side; window_index++) {
            if (window_index !== index) { //ignore self
                if (is_circular === false) {
                    if (window_index >= 0 && window_index < len) { //only when in bounds
                        if (hist[window_index] > current_value) {
                            is_highest = false; //someone else is bigger...
                            break;
                        }
                        //what if equal - i.e. if 3 or more thing are same height we should pick the middle one
                    }
                } else {
                    let t_index = window_index;
                    if (window_index < 0) {
                        t_index = len + window_index;
                    } else if (window_index >= len) {
                        t_index = window_index - len + 1; //256 -> 1
                    }
                    if (hist[t_index] > current_value) {
                        is_highest = false; //someone else is bigger...
                        break;
                    }
                }
            }
        }
        if (is_highest) {
            if (current_value !== 0) {
                output.push(index);
            }
        }
    }
    return output;
    
    
}

function filled_array(size, value) {
    return Array(size).fill(value);
}


function max_of_histogram(hist) {
    return hist.reduce((max, cur) => Math.max(max, cur), 0);
}

function number_of_samples_in_histogram(hist, sample_size = 1) {
    const total = hist.reduce((value, acc) => value + acc, 0);
    return Math.round(total / sample_size);
}

function normalize_histogram(hist) {
    const max = hist.reduce((max, cur) => Math.max(max, cur), 0);
    if (max === 0) {
        return filled_array(hist.length, 0);
    }
    return hist.map(x => x / max);
}

function draw_histogram_line(canvas2d, x, y, height, histogram, scale, colour) {
    //draw the line of the histogram...
    for (let index = 0; index < histogram.length - 1; index++) {
        let col = [200,200,200];
        if (colour === "hue") { //HUE
            const hue = (index * 2) / 360.0;
            col = hslToRgb(hue, 1.0, 0.5);
        } else if (colour === "saturation") {
        
        } else if (colour === "luminosity") {
            col = [index / 1.5 + 63, index / 1.5 + 63, index / 1.5 + 63];
        }
        
        // console.log(h3+' '+y_offset);
        canvas2d.line(
            x + (index * 2), y - (Math.round((histogram[index] / scale) * height)),
            x + ((index + 1) * 2), y - (Math.round((histogram[index + 1] / scale) * height)),
            col
        )
    }
}

function normalize(value, max) {
    if (max === 0) {
        return 0;
    }
    return value / max;
}

function remove_low_signal(hist, signal = 0.001) {
    const nos = number_of_samples_in_histogram(hist);
    const threshold = nos * signal;
    return hist.map(x => {
        if (x < threshold) {
            return 0;
        } else {
            return x;
        }
    })
}

class Histogram {
    constructor(running_samples = 5) {
        this.samples = null;
        this.running_samples = running_samples;
        this.width = null;
    }
    
    addSample(sample) {
        const width = sample.length;
        if (this.width !== width) {
            console.log('resettign samples for histogram');
            this.samples = [];
            this.width = width;
        }
        this.samples.push(sample);
        while (this.samples.length > this.running_samples) {
            this.samples.shift();
        }
    }
    
    reset() {
        this.samples = [];
        this.width = null;
    }
    
    average() {
        let avg = filled_array(this.width, 0);
        this.samples.forEach(sample => {
            sample.forEach((value, index) => {
                avg[index] += value;  //add up all values...
            })
        });
        const len = this.samples.length;
        if (len > 0) {
            return avg.map(value => Math.round(value / len));
        }
        return avg;
    }
}
