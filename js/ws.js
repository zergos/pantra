var ws = new WebSocketClient();
ws.open(`ws://${hostname}/ws/${session_id}`);

function send_message(message) {
    ws.send(serializer.encode(message));
}

ws.onopen = function (event) {
    send_message({C: 'RESTART'});
    drag_mode_active = false;
};

ws.onmessage = function (data, flags, number) {
    const received_msg = data.data;
    const fileReader = new FileReader();
    fileReader.onload = (res) => {
        let obj = serializer.decode(res.target.result);
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
                let element = get_node(v);
                if (!!element) {
                    se_log(`removing ${v} ${element.tagName}`);
                    element.remove();
                    delete_id(v);
                }
            }
            //root_node().style.visibility = 'hidden';
        } else if (obj.m === 'm') {
            let node = get_node(obj.l);
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
            let node = get_node(obj.l);
            send_message({C: 'V', oid: obj.l, value: node.value});
        } else if (obj.m === 'dm') {
            drag_mode_active = true;
        } else if (obj.m === 'log') {
            console.log(obj.l);
        }
    };
    fileReader.readAsArrayBuffer(received_msg);
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
