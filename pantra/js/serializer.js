let contentFilled = false;

let namespaces = {
    1: 'http://www.w3.org/1999/xhtml',
    2: 'http://www.w3.org/2000/svg',
    3: 'http://www.w3.org/2001/xml-events',
    4: 'http://www.w3.org/1999/xlink',
    5: 'http://www.w3.org/1998/Math/MathML',
};

function rootNode() {
    return document.getElementById('display');
}

function rebindNode(v, element) {
    let parent = element.parentNode;
    parent.removeChild(element);
    parent.appendChild(element);
}

function localizeDate(flag, v) {
    if (flag) {
        v.setMinutes(v.getMinutes() - v.getTimezoneOffset());
        return v;
    }
    return v;
}

const HTMLElementSerializer = {
    name: 'h',
    decode: function(s, v) {
        let element =  OID.node(v.i);
        let is_new = false;
        if (!element) {
            parent = OID.node(v.p);
            if (!parent) {
                if (v.p === null)
                    seLog(`element #${v.i} <${v.n}> created in root node`);
                else
                    seLog(`element #${v.i} <${v.n}> created in root node (#${v.p} not found)`);
                parent = rootNode();
                if (!contentFilled) {
                    parent.innerText = '';
                    contentFilled = true;
                }
            } else {
                seLog(`element #${v.i} <${v.n}> created with parent #${v.p}`);
            }
            if ('x' in v)
                element = document.createElementNS(namespaces[v.x], v.n);
            else
                element = document.createElement(v.n);
            if (config.JS_ADD_IDS)
                element.setAttribute('id',  `o${v.i}`);

            //element.typical = true;
            OID.set(element, v.i);
            parent.appendChild(element);
            is_new = true;

            if (v.type !== undefined)
                element.type = v.type;
        } else if (v['#'])
            rebindNode(v, element);
        for (let at in v.a) {
            if (!processSpecialAttribute(at, v.a[at], element, v.i, is_new))
                if (v.a[at])
                    element.setAttribute(at, v.a[at]);
                else
                    element.removeAttribute(at);
        }
        if (v.C || v['$']) {
            //element.className = v.C;
            let lst = [];
            if (v['$']) lst.push(v['$']);
            if (v.C) lst.push(v.C);
            element.setAttribute('class', lst.join(' '));
        } else
            element.removeAttribute('class');
        if (v.s)
            element.setAttribute('style', v.s);
        else
            element.removeAttribute('style');
        if (v.T !== undefined) {
            if (v.T !== element.innerHTML) element.innerHTML = v.T;
        } else if (v.t !== null) {
            if (v.t !== element.textContent)
                element.textContent = v.t;
        } /*else
            element.firstChild.nodeValue = v.t || '';*/
        if (v.f)
            element.focus();
        if (v.v !== undefined)
            if (v.type === 'checkbox' || v.type === 'radio') element.checked = v.v;
            else if (v.v === '') element.value = '';
            else if (v.type === 'number') element.valueAsNumber = v.v;
            else if (v.type === 'time') element.valueAsDate = localizeDate(v.l, v.v);
            else if (v.type === 'date') element.valueAsDate = localizeDate(v.l, v.v);
            else element.value = v.v;
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
            if (config.JS_ADD_IDS)
                element.setAttribute('id',  `o${v.i}`);
            OID.set(element, v.i);
            parent.appendChild(element);
        } else if (v['#'])
            rebindNode(v, element);
        element.textContent = v.t;
        return element;
    }
};

const StubElementSerializer = {
    name: 'd',
    decode: function (s, v) {
        let element = OID.node(v.i);
        if (!element) {
            parent = OID.node(v.p);
            if (!parent) {
                if (v.p === null)
                    seLog(`stub #${v.i} created in root node`);
                else
                    seLog(`stub #${v.i} created in root node (#${v.p} not found)`);
                parent = rootNode();
                if (!contentFilled) {
                    parent.innerText = '';
                    contentFilled = true;
                }
            } else {
                seLog(`stub #${v.i} created with parent #${v.p}`);
            }
            element = document.createElement('div');
            if (config.JS_ADD_IDS)
                element.setAttribute('id',  `o${v.i}`);
            if (v['$'])
                element.setAttribute('class', v['$']);
            
            OID.set(element, v.i);
            parent.appendChild(element);
        }
    }
};

const EventSerializer = {
    name: 'e',
    decode: function (s, v) {
        for (let attr in v.a) {
            if (attr.startsWith('on:'))
                processEventAttribute(v.ctx, v.a.selector || "", attr, v.a[attr], v.oid);
        }
    }
};

let fmt = {
    dateFormat: new Intl.DateTimeFormat(undefined, {dateStyle: 'short'}),
    timeFormat: new Intl.DateTimeFormat(undefined, {timeStyle: 'short'})
};

const DateSerializer = {
    name: 'D',
    match: function (s, v) {
        return v instanceof Date;
    },
    decode: function (s, v) {
        let d = new Date(v);
        //d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d;
    },
    encode: function (s, v) {
        return v.getTime()
    }
};

const TimeSerializer = {
    name: 'T',
    decode: function (s, v) {
        let d = new Date(v);
        //d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d;
    },
};

const ScriptSerializer = {
    name: 's',
    decode: function(s, v) {
        if (!SCRIPTS.exists(v.u)) {
            let script = document.createElement('script');
            SCRIPTS.new(script, v.u);
            document.getElementsByTagName("head")[0].appendChild(script);

            for (let at in v.a) {
                if (v.a[at])
                    script.setAttribute(at, v.a[at]);
            }

            if (v.t) script.textContent = v.t;
        }

        let element =  OID.node(v.i);
        if (!element) {
            let parent = OID.node(v.p);
            if (!parent) {
                parent = rootNode();
                if (!contentFilled) {
                    parent.innerText = '';
                    contentFilled = true;
                }
            }
            element = document.createElement('script');
            OID.set(element, v.i);
            parent.appendChild(element);
        }

        SCRIPTS.addref(v.u, v.i);
        return element;
    }
};


const serializer = new bsdf.BsdfSerializer(
    [DateSerializer, TimeSerializer, HTMLElementSerializer, TextSerializer, EventSerializer, ScriptSerializer,
    StubElementSerializer]);

