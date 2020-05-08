let _serializer_debug = false;
//let _create_control_tags = false;
let content_filled = false;

function se_log(message) {
    if (_serializer_debug) console.log(message);
}

function root_node() {
    return document.getElementById('display');
}

const HTMLElementSerializer = {
    name: 'h',
    decode: function(s, v) {
        let element =  get_node(v.i);
        let is_new = false;
        if (!element) {
            let parent = get_node(v.p);
            //while (parent && !parent.typical) parent = parent.parent;
            if (!parent) {
                //console.error(`parent ${v.p} not found for ${v.i} ${v.n}`);
                //return null;
                parent = root_node();
            }
            element = document.createElement(v.n);
            //element.typical = true;
            set_oid(element, v.i);
            se_log(`element ${v.i} ${v.n} created`);
            parent.appendChild(element);
            is_new = true;
        }
        for (let at in v.a) {
            if (!process_special_attribute(at, v.a[at], element, v.i, is_new))
                if (!!v.a[at])
                    element.setAttribute(at, v.a[at]);
                else
                    element.removeAttribute(at);
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

const ContextSerializer = {
    name: 'c',
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            if (!parent) {
                parent = root_node();
                if (!content_filled) {
                    parent.innerText = '';
                    content_filled = true;
                }
            }
            element = document.createElement(v.n);
            set_oid(element, v.i);
            element.className = 'default ctx-'+v.n;
            parent.appendChild(element);
        }
        return element;
    }
};

const ConditionSerializer = {
    name: 'i',
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            if (!parent) {
                console.error(`parent ${v.p} not found for condition ${v.i}`);
                return null;
            }
            element = document.createElement('condition');
            set_oid(element, v.i);
            parent.appendChild(element);
        }
        return element;
    }
};

const LoopSerializer = {
    name: 'l',
    decode: function(s, v) {
        let element = get_node(v.i);
        if (!element) {
            let parent = get_node(v.p);
            if (!parent) {
                console.error(`parent ${v.p} not found for loop ${v.i}`);
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

const TextSerializer = {
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

const EventSerializer = {
    name: 'e',
    decode: function (s, v) {
        return null;
    }
};

const serializer = new bsdf.BsdfSerializer(
    [HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer, EventSerializer]);

