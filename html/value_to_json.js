function value_to_json(value) {
    if (value === null) {
        return 'null';
    }
    if (value === undefined) {
        return 'null';
    }
    //DEAL WITH +/- INF at your leisure - null instead..
    //https://stackoverflow.com/questions/1423081/json-left-out-infinity-and-nan-json-status-in-ecmascript
    const type = typeof value;
    //handle as much by what exists
    if (['string', 'boolean', 'number', 'function'].includes(type)) {
        return JSON.stringify(value)
    } else if (Object.prototype.toString.call(value) === '[object Object]') {
        let parts = [];
        for (let k in value) {
            if (Object.prototype.hasOwnProperty.call(value, k)) {
                parts.push(JSON.stringify(k) + ': ' + value_to_json(value[k]));
            }
        }
        return '{' + parts.join(',') + '}';
    }
    //https://github.com/DavidBruant/Map-Set.prototype.toJSON/issues/16
    //stackoverflow.com/questions/43704904/how-to-stringify-objects-containing-es5-sets-and-maps
    //But these DO NOT RESPECT THE ORDER of the keys, NOT POSSIBLE with JSON.stringify
    //https://stackoverflow.com/questions/31190885/json-stringify-a-set
    else if (value instanceof Map) {
        let parts_in_order = [];
        value.forEach((entry, key) => {
            if (typeof key === 'string') {
                parts_in_order.push(JSON.stringify(key) + ':' + value_to_json(entry));
            } else {
                console.log('Non String KEYS in MAP not directly supported');
            }
            //FOR OTHER KEY TYPES ADD CUSTOM... 'Key' encoding...
        });
        return '{' + parts_in_order.join(',') + '}';
    }
    else if (typeof value[Symbol.iterator] !== "undefined") {
        //Other iterables like SET (also in ORDER)
        let parts = [];
        for (let entry of value) {
            parts.push(value_to_json(entry))
        }
        return '[' + parts.join(',') + ']';
    } else {
        return JSON.stringify(value)
    }
}

/*   let m = new Map();
   m.set('first', 'first_value');
   m.set('second', 'second_value');
   let m2 = new Map();
   m2.set('nested', 'nested_value');
   m.set('sub_map', m2);
   let map_in_array = new Map();
   map_in_array.set('key', 'value');
   let set1 = new Set(["1",2,3.0,4]);

   m2.set('array_here', [map_in_array, "Hello", true, 0.1, null, undefined, Number.POSITIVE_INFINITY, {"a": 4}]);
   m2.set('a set: ', set1);
   const test = {
       "hello": "ok",
       "map": m
   };

   console.log(value_to_json(test));*/