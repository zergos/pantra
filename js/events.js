function do_none(event) {
    event.stopPropagation();
    event.preventDefault();
}

class SimpleListener {
    constructor(method, oid) {
        this.method = method;
        this.oid = oid;
    }
    handleEvent(event) {
        event.stopPropagation();
        process_click(this.method, this.oid);
    }
}

class SimpleCommonListener {
    constructor(method) {
        this.method = method;
    }
    handleEvent(event) {
        event.stopPropagation();
        process_click(this.method, get_oid(event.target));
    }
}

let drag_mode_active = false;
let drag_events_attached = false;
class DragListener {
    constructor(method, oid) {
        this.method = method;
        this.oid = oid;
    }
    handleEvent(event) {
        event.stopPropagation();
        process_drag_start(this.method, this.oid, event);
    }
}

class DragCommonListener {
    constructor(method) {
        this.method = method;
    }
    handleEvent(event) {
        event.stopPropagation();
        process_drag_start(this.method, get_oid(event.target), event);
    }
}

function process_special_attribute(attr, value, node, oid, is_new = false) {
    if (attr.slice(0, 3) === 'on:' && attr !== 'on:drag') {
        if (is_new) {
            node.addEventListener(attr.slice(3), new SimpleListener(value, oid));
            if (attr === 'on:click')
                node.addEventListener('mousedown', do_none);
        }
        return true;
    } else if (attr === 'on:drag') {
        if (is_new) {
            node.addEventListener('dragstart', do_none);
            node.addEventListener('selectstart', do_none);
            node.addEventListener('mousedown', new DragListener(value, oid));
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
            if (drag_mode_active) do_none(event);
        });
        root.addEventListener('dragstart', (event) => {
            if (drag_mode_active) do_none(event);
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

function process_event_attribute(ctx, selector, attr, value) {
    if (event_registered.includes(selector)) return;
    event_registered.push(selector);

    if (attr.slice(0, 3) === 'on:' && attr !== 'on:drag') {
        addEventHandler(attr.slice(3), selector, new SimpleCommonListener(value));
        if (attr === 'on:click')
            addEventHandler('mousedown', selector, do_none);
    } else if (attr === 'on:drag') {
        addEventHandler('dragstart', selector, do_none);
        addEventHandler('selectstart', selector, do_none);
        addEventHandler('mousedown', selector, new DragCommonListener(value));
        attach_drag_events();
    }
}

function addEventHandler(type, selector, listener) {
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

function process_events(type, event) {
    let node = event.target;
    for (let row of event_tab[type]) {
        if (!node.matches(row.selector)) continue;
        if (row.listener instanceof Function) row.listener(event);
        else row.listener.handleEvent(event);
    }
}
