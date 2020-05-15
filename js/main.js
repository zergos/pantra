var main = new WSClient(`ws://${hostname}/ws/${session_id}`);

function send_message(message) {
    main.send(serializer.encode(message));
}

main.onrefresh = () => {
    send_message({'C': 'UP'})
};

main.onmessage = (data) => {
    let obj = serializer.decode(data);
    switch (obj.m) {
        case 'u':
            //root_node().style.visibility = 'visible';
            break;

        case 'c':
            let display = root_node();
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
                    se_log(`removing ${v} ${element.tagName}`);
                    element.remove();
                    OID.delete(v);
                }
            }
            //root_node().style.visibility = 'hidden';
            break;

        case 'm': {
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
            break;
        }

        case 'v': {
            let node = OID.node(obj.l);
            send_message({C: 'V', oid: obj.l, value: node.value});
            break;
        }

        case 'dm':
            drag_mode_active = true;
            break;

        case 'log':
            console.log(obj.l);
            break;

        case 'rst':
            root_node().textContent = '';
            OID.clear();
            drag_mode_active = false;
            break;

        case 'app':
            document.location = obj.l;
            break;
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
