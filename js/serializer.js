let _serializer_debug = false;
function se_log(message) {
    if (_serializer_debug) console.log(message);
}

function root_node() {
    return document.getElementById('display');
}

const HTMLElementSerializer = {
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
            if (!!child)
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

const ContextSerializer = {
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
            if (!!child)
                element.appendChild(child);
        }
        return element;
    }
};

const ConditionSerializer = {
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

const LoopSerializer = {
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

const TextSerializer = {
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

const EventSerializer = {
    name: 'E',
    decode: function (s, v) {
        let selector = v.a.selector;
        for (let attr in v.a) {
            if (attr !== 'selector')
                process_event_attribute(v.ctx, selector, attr, v.a[attr]);
        }
    }
};

const HTMLElementSerializerU = {
    name: 'h',
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

const ContextSerializerU = {
    name: 'c',
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

const ConditionSerializerU = {
    name: 'i',
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

const LoopSerializerU = {
    name: 'l',
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

const TextSerializerU = {
    name: 't',
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

const EventSerializerU = {
    name: 'e',
    decode: function (s, v) {
        // stub
    }
};

const serializer = new bsdf.BsdfSerializer(
    [HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer, EventSerializer,
    HTMLElementSerializerU, ContextSerializerU, ConditionSerializerU, LoopSerializerU, TextSerializerU, EventSerializerU]);

function do_none(event) {
    event.stopPropagation();
    event.preventDefault();
}

class ClickListener {
    constructor(method) {
        this.method = method;
    }
    handleEvent(event) {
        event.stopPropagation();
        process_click(this.method, parseInt(event.target.id));
    }
}

let drag_mode_active = false;
let drag_events_attached = false;
class DragListener {
    constructor(method) {
        this.method = method;
    }
    handleEvent(event) {
        event.stopPropagation();
        process_drag_start(this.method, parseInt(event.target.id), event);
    }
}

function process_special_attribute(attr, value, node, oid, is_new = false) {
    if (attr === 'on:click') {
        if (is_new) {
            node.addEventListener('click', new ClickListener(value));
            node.addEventListener('mousedown', do_none);
        }
        return true;
    } else if (attr === 'on:drag') {
        if (is_new) {
            node.addEventListener('dragstart', do_none);
            node.addEventListener('selectstart', do_none);
            node.addEventListener('mousedown', new DragListener(value));
            attach_drag_events();
        }
        return true;
    }
    return false;
}

function attach_drag_events() {
    if (!drag_events_attached) {
        drag_events_attached = true;
        let root = root_node();
        root.addEventListener('selectstart', (event) => {
            if (drag_mode_active) event.stopPropagation();
        });
        root.addEventListener('dragstart', (event) => {
            if (drag_mode_active) event.stopPropagation();
        });
        root.addEventListener('mousemove', (event) => {
            if (drag_mode_active) {
                event.stopPropagation();
                process_drag_move(event);
            }
        });
        root.addEventListener('mouseup', (event) => {
            if (drag_mode_active) {
                event.stopPropagation();
                process_drag_stop(event);
                drag_mode_active = false;
            }
        });
    }
}

let event_registered = [];
let event_tab = {}; //Dict['event', List[Dict['selector,listener', data]]]
let events_attached = false;

function process_event_attribute(ctx, selector, attr, value) {
    if (event_registered.includes(selector)) return;
    event_registered.push(selector);
    attach_events();

    if (attr === 'on:click') {
        addEventHandler('click', selector, new ClickListener(value));
        addEventHandler('mousedown', selector, do_none);
    } else if (attr === 'on:drag') {
        addEventHandler('dragstart', selector, do_none);
        addEventHandler('selectstart', selector, do_none);
        addEventHandler('mousedown', selector, new DragListener(value));
        attach_drag_events();
    }
}

function addEventHandler(type, selector, listener) {
    for (let row of event_tab[type])
        if (row.selector === selector)
            return;
    event_tab[type].push({selector: selector, listener: listener});
}

function attach_events() {
    if (!events_attached) {
        events_attached = true;
        let root = root_node();
        event_tab = ['click', 'mousedown', 'mousemove', 'mouseup', 'selectstart', 'dragstart'].reduce((o, k) => {
            o[k] = [];
            root.addEventListener(k, (event) => {process_events(k, event)});
            return o;
        }, {});
    }
}

function process_events(type, event) {
    let node = event.target;
    for (let row of event_tab[type]) {
        if (!node.matches(row.selector)) continue;
        if (row.listener instanceof Function) row.listener(event);
        else row.listener.handleEvent(event);
    }
}
