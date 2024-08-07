function process_message(obj) {
    switch (obj.m) {
        case 'u':
            //root_node().style.visibility = 'visible';
            break;

        case 'c':
            let display = rootNode();
            display.innerText = '';
            display.append(obj.l);
            break;

        case 'e':
            console.error(obj.l);
            break;

        case 'd':
            for (let v of obj.l) {
                let element = OID.node(v);
                if (!!element) {
                    seLog(`removing ${v} ${element.tagName}`);
                    element.remove();
                    OID.delete(v);
                } else {
                    seLog(`element ${v} not found for removing`)
                }
            }
            //root_node().style.visibility = 'hidden';
            break;

        case 'm': {
            let node = OID.node(obj.l);
            let rect = node.getBoundingClientRect();
            sendMessage(Messages.metrics(obj.l, rect));
            break;
        }

        case 'v': {
            let node = OID.node(obj.l);
            let value;
            if (obj.t === 'number' || obj.t === 'time') value = node.valueAsNumber;
            else if (obj.t === 'date') value = node.valueAsDate;
            else value = node.value;
            sendMessage(Messages.value(obj.l, value));
            break;
        }

        case 'dm':
            protoLog("drag mode active");
            drag_mode_active = true;
            break;

        case 'log':
            console.log(obj.l);
            break;

        case 'call':
            protoLog(`calling ${obj.method}`);
            let functionName = obj.method;
            if (typeof(window[functionName]) === "function")
                window[functionName].apply(null, obj.args);
            break;

        case 'rst':
            protoLog("restart");
            let root = rootNode();
            let parent = root.parentElement;
            root.remove();
            OID.clear();
            root = document.createElement('div');
            root.id = 'display';
            parent.appendChild(root);
            drag_mode_active = false;
            drag_events_attached = false;
            resetEvents();
            break;

        case 'recon':
            protoLog("reconnect");
            wsConnection.reopen();
            break;

        case 'app':
            document.location.href = obj.l;
            break;

        case 'title':
            document.title = obj.l;
            break;

        case 'valid':
            let node = OID.node(obj.l);
            sendMessage(Messages.validity(obj.l, node.validity.valid));
            break;

        case 'koff':
            keyEventsDisabled = true;
            break;

        case 'kon':
            keyEventsDisabled = false;
            break;
    }
}

let Messages = {
    up: () => { return {C: "UP"} },
    refresh: () => { return {C: "REFRESH"} },
    click: (method, oid) => { return {C: "CLICK", method: method, oid: oid} },
    change: (method, oid, value) => { return {C: "CHANGE", method: method, oid: oid, x: value} },
    dragStart: (method, oid, event) => { return {C: 'DD', method: method, oid: oid, x: event.pageX, y: event.pageY, button: event.button} },
    dragMove: (event) => { return {C: 'DM', x: event.pageX, y: event.pageY} },
    dragStop: (event) => { return {C: 'DU', x: event.pageX, y: event.pageY} },
    select: (method, oid, opts) => { return {C: 'SELECT', method: method, oid: oid, opts: opts} },
    value: (oid, value) => { return {C: 'V', oid: oid, value: value} },
    bindValue: (variable, oid, value) => { return {C: 'B', v: variable, oid: oid, x: value} },
    key: (method, oid, key) => { return {C: 'KEY', method: method, oid: oid, key: key} },
    call: (oid, method, args) => { return {C: 'CALL', oid: oid, method: method, args: args} },
    metrics: (oid, rect) => {
        return {
                C: 'M',
                oid: oid,
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                w: Math.round(rect.width),
                h: Math.round(rect.height)
            }
    },
    validity: (oid, validity) => { return {C: 'VALID', oid: oid, validity: validity} },
};
