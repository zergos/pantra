var main = new WSClient(`ws://${hostname}/ws/${session_id}`);

function send_message(message) {
    main.send(serializer.encode(message));
}

main.onrefresh = () => {
    send_message({'C': 'UP'})
};

main.onmessage = (data) => {
    let obj = serializer.decode(data);
    if (obj.m === 'u') {
        //root_node().style.visibility = 'visible';
    } else if (obj.m === 'c') {
        let display = root_node();
        display.innerText = '';
        display.append(obj.l);
    } else if (obj.m === 'e') {
        console.error(obj.l);
    } else if (obj.m === 'd') {
        for (let v of obj.l) {
            let element = OID.node(v);
            if (!!element) {
                se_log(`removing ${v} ${element.tagName}`);
                element.remove();
                OID.delete(v);
            }
        }
        //root_node().style.visibility = 'hidden';
    } else if (obj.m === 'm') {
        let node = OID.node(obj.l);
        let rect = node.getBoundingClientRect();
        send_message({
            C: 'M',
            oid: obj.l,
            x: Math.round(rect.left),
            y: Math.round(rect.top),
            w: Math.round(rect.width),
            h: Math.round(rect.height)
        });
    } else if (obj.m === 'v') {
        let node = OID.node(obj.l);
        send_message({C: 'V', oid: obj.l, value: node.value});
    } else if (obj.m === 'dm') {
        drag_mode_active = true;
    } else if (obj.m === 'log') {
        console.log(obj.l);
    } else if (obj.m === 'rst') {
        root_node().textContent = '';
        OID.clear();
        drag_mode_active = false;
    }
};

function process_click(method, oid) {
    send_message({C: 'CLICK', method: method, oid: oid});
}

function process_drag_start(method, oid, event) {
    send_message({C: 'DD', method: method, oid: oid, x: event.pageX, y: event.pageY, button: event.button});
}

function process_drag_move(event) {
    send_message({C: 'DM', x: event.pageX, y: event.pageY});
}

function process_drag_stop(event) {
    send_message({C: 'DU', x: event.pageX, y: event.pageY});

}

function process_select(method, oid, options) {
    let opts = Object.values(options).reduce((acc, cur) => {
        acc.push(OID.get(cur));
        return acc;
    }, []);
    send_message({C: 'SELECT', method: method, oid: oid, opts: opts});
}

function process_bind_value(variable, oid, value) {
    send_message({C: 'B', v: variable, oid: oid, x: value})
}

send_message({C: 'REFRESH'});
