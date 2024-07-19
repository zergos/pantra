function doNothing(event) {
    event.stopPropagation();
    event.preventDefault();
}

class EventListener {
    constructor(method, oid=null) {
        this.method = method;
        this.oid = oid;
    }
    getOid(event) {
        return this.oid || OID.get(event.target);
    }
    handleEvent(event) {
        event.stopPropagation();
    }
}

class DefaultListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        processClick(this.method, this.getOid(event));
        let tagName = event.target.tagName.toLowerCase();
        if (tagName === 'button' || tagName === 'form') {// prevent submit
            event.preventDefault();
            return false;
        }
    }
}

class ChangeListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        processChange(this.method, this.getOid(event), event.target);
    }
}

class SelectListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        processSelect(this.method, this.getOid(event), event.target.selectedOptions);
    }
}

class ValueListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        processBindValue(this.method, this.getOid(event), event.target);
    }
}

class KeyListener extends EventListener {
    constructor(method, key, oid=null) {
        super(method, oid);
        this.key = key;
    }
    handleEvent(event) {
        super.handleEvent(event);
        if (event.key !== undefined && (!this.key || event.key === this.key)) {
            let visible;
            let node = event.target;
            if (node) {
                let box = node.getBoundingClientRect();
                visible = box.width && box.height;
            } else {
                visible = true;
            }
            if (visible)
                processKey(this.method, this.getOid(event), event.key);
        }
    }
}

let dragModeActive = false;
let dragEventsAttached = false;
class DragListener extends EventListener {
    handleEvent(event) {
        super.handleEvent(event);
        processDragStart(this.method, this.getOid(event), event);
    }
}

function attachDragEvents() {
    if (!dragEventsAttached) {
        dragEventsAttached = true;
        seLog("drag events attached");
        let root = rootNode();
        root.addEventListener('selectstart', (event) => {
            if (dragModeActive) doNothing(event);
        });
        root.addEventListener('dragstart', (event) => {
            if (dragModeActive) doNothing(event);
        });
        root.addEventListener('mousemove', (event) => {
            if (dragModeActive) {
                event.stopPropagation();
                processDragMove(event);
            }
        });
        root.addEventListener('mouseup', (event) => {
            if (dragModeActive) {
                event.stopPropagation();
                processDragStop(event);
                dragModeActive = false;
                seLog("drag mode disabled")
            }
        });
    }
}

function addEvent(eventCode, selector, method, oid) {
    if (eventCode === 'on:select') {
        addEventHandler('change', selector, new SelectListener(method, oid));
    } else if (eventCode === 'on:drag') {
        addEventHandler('dragstart', selector, doNothing);
        addEventHandler('selectstart', selector, doNothing);
        addEventHandler('mousedown', selector, new DragListener(method, oid));
        attachDragEvents();
    } else if (eventCode.startsWith('on:keyup') || eventCode.startsWith('on:keydown')) {
        let chunks = eventCode.split(':');
        let key = chunks.length > 2 ? chunks[2] : null;
        addEventHandler(chunks[1], selector, new KeyListener(method, key, oid));
    } else if (eventCode === "on:change") {
        addEventHandler("change", selector, new ChangeListener(method, oid));
    } else if (eventCode.startsWith('on:')) {
        addEventHandler(eventCode.slice(3), selector, new DefaultListener(method, oid));
        /*if (attr === 'on:click')
            addEventHandler('mousedown', selector, doNothing);*/
    } else {
        console.log(`wrong event ${eventCode}`);
    }
}

let eventRegistered = [];
let eventTab = {}; //dict['event', list[dict['selector,listener', data]]]
let keyEventsDisabled = false;

function addEventHandler(eventName, selector, listener) {
    if (selector instanceof Element) {
        selector.addEventListener(eventName, listener);
        return;
    }

    if (!(eventName in eventTab)) {
        eventTab[eventName] = [];
        rootNode().addEventListener(eventName, (event) => processEvents(eventName, event));
    }
    else
        for (let row of eventTab[eventName])
            if (row.selector === selector)
                return;
    eventTab[eventName].push({selector: selector, listener: listener});
}

function processSpecialAttribute(attr, value, node, oid, isNew = false) {
    if (attr.startsWith('on:')) {
        if (isNew)
            addEvent(attr, node, value, oid);
        return true;
    }
    if (attr === 'bind:value') {
        if (isNew) {
            if (node.tagName === 'INPUT')
                node.addEventListener('input', new ValueListener(value, oid));
            else
                node.addEventListener('change',  new ValueListener(value, oid));
        }
        return true;
    }
    if (['checked', 'required', 'disabled'].includes(attr)) {
        node[attr] = !!value;
        return true;
    }
    return false;
}

function processEventAttribute(ctxName, selector, eventCode, method, oid) {
    if (!selector) {
        if (eventRegistered.includes(ctxName + eventCode)) return;
        eventRegistered.push(ctxName + eventCode);
        addEvent(eventCode, "", method, oid);
    } else {
        if (eventRegistered.includes(selector + eventCode)) return;
        eventRegistered.push(selector + eventCode);
        addEvent(eventCode, selector, method, null);
    }
}

function processEvents(type, event) {
    if (['keyup', 'keydown'].includes(type) && keyEventsDisabled)
        return;
    let node = event.target;
    for (let row of eventTab[type]) {
        if (row.selector && !node.matches(row.selector)) continue;
        if (row.listener instanceof Function) row.listener(event);
        else row.listener.handleEvent(event);
    }
}

function resetEvents() {
    eventRegistered = [];
    eventTab = {};
}