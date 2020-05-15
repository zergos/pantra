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

let drag_mode_active = false;
let drag_events_attached = false;
class DragListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        process_drag_start(this.method, this.get_oid(event), event);
    }
}

function process_special_attribute(attr, value, node, oid, is_new = false) {
    if (attr === 'on:change' && node.tagName === 'SELECT') {
        if (is_new) {
            node.addEventListener('change', new SelectListener(value, oid));
        }
        return true;
    } else if (attr.slice(0, 3) === 'on:' && attr !== 'on:drag') {
        if (is_new) {
            node.addEventListener(attr.slice(3), new SimpleListener(value, oid));
            if (attr === 'on:click')
                node.addEventListener('mousedown', do_nothing);
        }
        return true;
    } else if (attr === 'on:drag') {
        if (is_new) {
            node.addEventListener('dragstart', do_nothing);
            node.addEventListener('selectstart', do_nothing);
            node.addEventListener('mousedown', new DragListener(value, oid));
            attach_drag_events();
        }
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

let event_registered = [];
let event_tab = {}; //Dict['event', List[Dict['selector,listener', data]]]

function process_event_attribute(ctx, selector, attr, value) {
    if (event_registered.includes(selector + attr)) return;
    event_registered.push(selector + attr);

    if (attr === 'on:change' && node.tagName === 'select') {
        addEventHandler('change', selector, new SelectListener(value));
    } else if (attr.slice(0, 3) === 'on:' && attr !== 'on:drag') {
        addEventHandler(attr.slice(3), selector, new SimpleListener(value));
        if (attr === 'on:click')
            addEventHandler('mousedown', selector, do_nothing);
    } else if (attr === 'on:drag') {
        addEventHandler('dragstart', selector, do_nothing);
        addEventHandler('selectstart', selector, do_nothing);
        addEventHandler('mousedown', selector, new DragListener(value));
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
