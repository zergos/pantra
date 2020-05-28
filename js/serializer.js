let _serializer_debug = false;
//let _create_control_tags = false;
let content_filled = false;

let namespaces = {
    1: 'http://www.w3.org/1999/xhtml',
    2: 'http://www.w3.org/2000/svg',
    3: 'http://www.w3.org/2001/xml-events',
    4: 'http://www.w3.org/1999/xlink',
    5: 'http://www.w3.org/1998/Math/MathML'
};

function se_log(message) {
    if (_serializer_debug) console.log(message);
}

function root_node() {
    return document.getElementById('display');
}

function rebind_node(v, element) {
    if (v['#'] === undefined) return;
    let parent = element.parentNode;
    parent.removeChild(element);
    parent.appendChild(element);
}

const HTMLElementSerializer = {
    name: 'h',
    decode: function(s, v) {
        let element =  OID.node(v.i);
        let is_new = false;
        if (!element) {
            let parent = OID.node(v.p);
            if (!parent) {
                se_log(`element became new root node:`);
                parent = root_node();
            }
            if ('x' in v)
                element = document.createElementNS(namespaces[v.x], v.n);
            else
                element = document.createElement(v.n);

            //element.typical = true;
            OID.set(element, v.i);
            se_log(`element ${v.i} ${v.n} created`);
            parent.appendChild(element);
            is_new = true;
        } else
            rebind_node(v, element);
        for (let at in v.a) {
            if (!process_special_attribute(at, v.a[at], element, v.i, is_new))
                if (v.a[at])
                    element.setAttribute(at, v.a[at]);
                else
                    element.removeAttribute(at);
        }
        if (v.C)
            //element.className = v.C;
            element.setAttribute('class', v.C);
        else
            element.removeAttribute('class');
        if (v.s)
            element.setAttribute('style', v.s);
        else
            element.removeAttribute('style');
        if (is_new) {
            if (v.t) element.textContent = v.t;
        } else if (!element.firstElementChild) {
            if (v.t !== element.textContent)
                element.textContent = v.t;
        } else
            element.firstChild.nodeValue = v.t || '';
        if (v.f)
            element.focus();
        return element;
    }
};

const ContextSerializer = {
    name: 'c',
    decode: function(s, v) {
        let element = OID.node(v.i);
        if (!element) {
            let parent = OID.node(v.p);
            if (!parent) {
                parent = root_node();
                if (!content_filled) {
                    parent.innerText = '';
                    content_filled = true;
                }
            }
            element = document.createElement('c-'+v.n);
            OID.set(element, v.i);
            element.className = 'd '+v.n;
            parent.appendChild(element);
        } else
            rebind_node(v, element);
        return element;
    }
};

const ConditionSerializer = {
    name: 'i',
    decode: function(s, v) {
        let element = OID.node(v.i);
        if (!element) {
            let parent = OID.node(v.p);
            if (!parent) {
                console.error(`parent ${v.p} not found for condition ${v.i}`);
                return null;
            }
            element = document.createElement('condition');
            OID.set(element, v.i);
            parent.appendChild(element);
        }
        return element;
    }
};

const LoopSerializer = {
    name: 'l',
    decode: function(s, v) {
        let element = OID.node(v.i);
        if (!element) {
            let parent = OID.node(v.p);
            if (!parent) {
                console.error(`parent ${v.p} not found for loop ${v.i}`);
                return null;
            }
            element = document.createElement('loop');
            OID.set(element, v.i);
            se_log(`element ${v.i} ${v.n} created`);
            parent.appendChild(element);
        }
        return element;
    }
};

const TextSerializer = {
    name: 't',
    decode: function(s, v) {
        let element = OID.node(v.i);
        if (!element) {
            let parent = OID.node(v.p);
            element = document.createElement('text');
            OID.set(element, v.i);
            parent.appendChild(element);
        } else
            rebind_node(v, element);
        element.textContent = v.t;
        return element;
    }
};

const EventSerializer = {
    name: 'e',
    decode: function (s, v) {
        let selector = v.a.selector;
        for (let attr in v.a) {
            if (attr !== 'selector')
                process_event_attribute(v.ctx, selector, attr, v.a[attr]);
        }
    }
};

const serializer = new bsdf.BsdfSerializer(
    [HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer, EventSerializer]);

