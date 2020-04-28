let _serializer_debug = false;
function se_log(message) {
    if (_serializer_debug) console.log(message);
}

function root_node() {
    return document.getElementById('display');
}

var HTMLElementSerializer = {
    name: 'H',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.createElement(v.n);
        element.id = v.i;
        for (let child of v.c) {
            element.appendChild(child);
        }
        for (let at in v.a) {
            if (!process_special_attribute(at, v.a[at], element, v.i, true))
                element.setAttribute(at, v.a[at]);
        }
        if (!!v.C)
            element.className = v.C;
        if (!!v.t)
            element.innerText = v.t;
        if (!!v.s)
            element.setAttribute('style', v.s);
        return element;
    }
};

var ContextSerializer = {
    name: 'C',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.createElement(v.n);
        element.id = v.i;
        element.className = 'default ctx-'+v.n;
        for (let child of v.c) {
            element.appendChild(child);
        }
        return element;
    }
};

var ConditionSerializer = {
    name: 'I',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.createElement('condition');
        element.id = v.i;
        for (let child of v.c) {
            element.appendChild(child);
        }
        return element;
    }
};

var LoopSerializer = {
    name: 'L',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.createElement('loop');
        element.id = v.i;
        for (let child of v.c) {
            element.appendChild(child);
        }
        return element;
    }
};

var TextSerializer = {
    name: 'T',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.createElement('raw');
        element.id = v.i;
        element.innerText = v.t;
        return element;
    }
};

var HTMLElementSerializerU = {
    name: 'H2',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.getElementById(v.i);
        let is_new = false;
        if (!element) {
            let parent = document.getElementById(v.p);
            if (!parent) {
                //console.error(`parent ${v.p} not found for ${v.i} ${v.n}`);
                //return null;
                parent = root_node();
            }
            element = document.createElement(v.n);
            element.id = v.i;
            se_log(`element ${v.i} ${v.n} created`);
            parent.appendChild(element);
            is_new = true;
        }
        for (let at in v.a) {
            if (!process_special_attribute(at, v.a[at], element, v.i, is_new))
                element.setAttribute(at, v.a[at]);
        }
        if (!!v.C)
            element.className = v.C;
        if (!!v.t)
            element.innerText = v.t;
        if (!!v.s)
            element.setAttribute('style', v.s);
        return element;
    }
};

var ContextSerializerU = {
    name: 'C2',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.getElementById(v.i);
        if (!element) {
            let parent = document.getElementById(v.p);
            if (!parent) parent = root_node();
            element = document.createElement(v.n);
            element.id = v.i;
            parent.appendChild(element);
        }
        return element;
    }
};

var ConditionSerializerU = {
    name: 'I2',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.getElementById(v.i);
        if (!element) {
            let parent = document.getElementById(v.p);
            element = document.createElement('condition');
            element.id = v.i;
            parent.appendChild(element);
        }
        for (let child of v.c) {
            element.appendChild(child);
        }
        return element;
    }
};

var LoopSerializerU = {
    name: 'L2',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.getElementById(v.i);
        if (!element) {
            let parent = document.getElementById(v.p);
            if (!parent) {
                console.error(`parent ${v.p} not found for ${v.i} ${v.n}`);
                return null;
            }
            element = document.createElement('loop');
            element.id = v.i;
            se_log(`element ${v.i} ${v.n} created`);
            parent.appendChild(element);
        }
        return element;
    }
};

var TextSerializerU = {
    name: 'T2',
    match: function(s, v) {
        return false;
    },
    encode: function(s, v) {
        return null;
    },
    decode: function(s, v) {
        let element = document.getElementById(v.i);
        if (!element) {
            let parent = document.getElementById(v.p);
            element = document.createElement('raw');
            element.id = v.i;
            parent.appendChild(element);
        }
        element.innerText = v.t;
        return element;
    }
};

var serializer = new bsdf.BsdfSerializer(
    [HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer,
    HTMLElementSerializerU, ContextSerializerU, ConditionSerializerU, LoopSerializerU, TextSerializerU]);

class ClickListener {
    constructor(method, oid) {
        this.method = method;
        this.oid = oid;
    }
    handleEvent(event) {
        process_click(this.method, this.oid)
    }
}

function process_special_attribute(attr, value, node, oid, is_new = false) {
    if (attr === 'on:click') {
        if (is_new)
            node.addEventListener('click', new ClickListener(value, oid));
        return true;
    }
    return false;
}