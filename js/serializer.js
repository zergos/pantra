let _serializer_debug = false;
function se_log(message) {
    if (_serializer_debug) console.log(message);
}

function root_node() {
    return document.getElementById('display');
}

const HTMLElementSerializer = {
    name: 'H',
    decode: function(s, v) {
        let element = document.createElement(v.n);
        set_oid(element, v.i);
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
    decode: function(s, v) {
        let element = document.createElement(v.n);
        set_oid(element, v.i);
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
    decode: function(s, v) {
        let element = document.createElement('condition');
        set_oid(element, v.i);
        for (let child of v.c) {
            element.appendChild(child);
        }
        return element;
    }
};

const LoopSerializer = {
    name: 'L',
    decode: function(s, v) {
        let element = document.createElement('loop');
        set_oid(element, v.i);
        for (let child of v.c) {
            element.appendChild(child);
        }
        return element;
    }
};

const TextSerializer = {
    name: 'T',
    decode: function(s, v) {
        let element = document.createElement('text');
        set_oid(element, v.i);
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
    decode: function(s, v) {
        let element =  get_node(v.i);
        let is_new = false;
        if (!element) {
            let parent = get_node(v.p);
            if (!parent) {
                //console.error(`parent ${v.p} not found for ${v.i} ${v.n}`);
                //return null;
                parent = root_node();
            }
            element = document.createElement(v.n);
            set_oid(element, v.i);
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
        else
            element.removeAttribute('class');
        if (!!v.t)
            element.innerText = v.t;
        if (!!v.s)
            element.setAttribute('style', v.s);
        else
            element.removeAttribute('style');
        if (v.f)
            element.focus();
        return element;
    }
};

const ContextSerializerU = {
    name: 'c',
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            if (!parent) parent = root_node();
            element = document.createElement(v.n);
            set_oid(element, v.i);
            parent.appendChild(element);
        }
        return element;
    }
};

const ConditionSerializerU = {
    name: 'i',
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            element = document.createElement('condition');
            set_oid(element, v.i);
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
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            if (!parent) {
                console.error(`parent ${v.p} not found for ${v.i} ${v.n}`);
                return null;
            }
            element = document.createElement('loop');
            set_oid(element, v.i);
            se_log(`element ${v.i} ${v.n} created`);
            parent.appendChild(element);
        }
        return element;
    }
};

const TextSerializerU = {
    name: 't',
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            element = document.createElement('text');
            set_oid(element, v.i);
            parent.appendChild(element);
        }
        element.innerText = v.t;
        return element;
    }
};

const EventSerializerU = {
    name: 'e',
    decode: function (s, v) {
        return null;
    }
};

const serializer = new bsdf.BsdfSerializer(
    [HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer, EventSerializer,
    HTMLElementSerializerU, ContextSerializerU, ConditionSerializerU, LoopSerializerU, TextSerializerU, EventSerializerU]);

