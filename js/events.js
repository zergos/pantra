function do_nothing(event) {
    event.stopPropagation();
    event.preventDefault();
}

class EventListener {
    constructor(method, oid=null) {
        this.method = method;
        this.oid = oid;
    }
    get_oid(event) {
        return this.oid || OID.get(event.target);
    }
    handleEvent(event) {
        event.stopPropagation();
    }
}

class SimpleListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        process_click(this.method, this.get_oid(event));
        if (event.target.tagName === 'button') // prevent submit
            event.preventDefault();
    }
}

class SelectListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        process_select(this.method, this.get_oid(event), event.target.selectedOptions);
    }
}

class ValueListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        process_bind_value(this.method, this.get_oid(event), event.target.value);
    }
}

class KeyListener extends EventListener {
    constructor(method, key, oid=null) {
        super(method, oid);
        this.key = key;
    }
    handleEvent(event) {
        super.handleEvent(event);
        if (!this.key || event.key === this.key)
            process_key(this.method, this.get_oid(event), event.key);
    }
}

let drag_mode_active = false;
let drag_events_attached = false;
class DragListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        process_drag_start(this.method, this.get_oid(event), event);
    }
}

function attach_drag_events() {
    if (!drag_events_attached) {
        drag_events_attached = true;
        let root = root_node();
        root.addEventListener('selectstart', (event) => {
            if (drag_mode_active) do_nothing(event);
        });
        root.addEventListener('dragstart', (event) => {
            if (drag_mode_active) do_nothing(event);
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

function addEvent(attr, selector, method, oid) {
    if (attr === 'on:select') {
        addEventHandler('change', selector, new SelectListener(method, oid));
    } else if (attr === 'on:drag') {
        addEventHandler('dragstart', selector, do_nothing);
        addEventHandler('selectstart', selector, do_nothing);
        addEventHandler('mousedown', selector, new DragListener(method, oid));
        attach_drag_events();
    } else if (attr.startsWith('on:keyup') || attr.startsWith('on:keydown')) {
        let chunks = attr.split(':');
        let key = chunks.length > 2 ? chunks[2]:null;
        addEventHandler(chunks[1], selector, new KeyListener(method, key, oid));
    } else if (attr.startsWith('on:')) {
        addEventHandler(attr.slice(3), selector, new SimpleListener(method, oid));
        /*if (attr === 'on:click')
            addEventHandler('mousedown', selector, do_nothing);*/
    }
}

let event_registered = [];
let event_tab = {}; //Dict['event', List[Dict['selector,listener', data]]]

function addEventHandler(type, selector, listener) {
    if (selector instanceof Element) {
        selector.addEventListener(type, listener);
        return;
    }

    if (!(type in event_tab)) {
        event_tab[type] = [];
        root_node().addEventListener(type, (event) => process_events(type, event));
    }
    else
        for (let row of event_tab[type])
            if (row.selector === selector)
                return;
    event_tab[type].push({selector: selector, listener: listener});
}

function process_special_attribute(attr, value, node, oid, is_new = false) {
    if (attr.startsWith('on:')) {
        if (is_new)
            addEvent(attr, node, value, oid);
        return true;
    } else if (attr === 'bind:value') {
        if (is_new) {
            if (node.tagName === 'INPUT')
                node.addEventListener('input', new ValueListener(value, oid));
            else
                node.addEventListener('change',  new ValueListener(value, oid));
        }
        return true;
    }
    return false;
}

function process_event_attribute(ctx, selector, attr, value, oid) {
    if (!selector) {
        if (event_registered.includes(ctx + attr)) return;
        event_registered.push(ctx + attr);
        addEvent(attr, "", value, oid);
    } else {
        if (event_registered.includes(selector + attr)) return;
        event_registered.push(selector + attr);
        addEvent(attr, selector, value, null);
    }
}

function process_events(type, event) {
    let node = event.target;
    for (let row of event_tab[type]) {
        if (row.selector && !node.matches(row.selector)) continue;
        if (row.listener instanceof Function) row.listener(event);
        else row.listener.handleEvent(event);
    }
}

function reset_events() {
    event_registered = [];
    event_tab = {};
}