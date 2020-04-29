var ws = new WebSocketClient();
ws.open(`ws://${hostname}/ws/${session_id}`);

function send_message(message) {
    ws.send(serializer.encode(message));
}

ws.onopen = function (event) {
    send_message({C: 'RESTART'});
};

ws.onmessage = function (data, flags, number) {
    const received_msg = data.data;
    const fileReader = new FileReader();
    fileReader.onload = (res) => {
        let obj = serializer.decode(res.target.result);
        if (obj.m === 'u') {
        } else if (obj.m === 'c') {
            let display = root_node();
            display.innerText = '';
            display.append(obj.l);
        } else if (obj.m === 'e') {
            console.error(obj.l);
        } else if (obj.m === 'd') {
            for (let v of obj.l) {
                let element = document.getElementById(v);
                if (!!element) {
                    se_log(`removing ${v} ${element.tagName}`);
                    element.remove();
                }
            }
        } else if (obj.m === 'm') {
            let node = document.getElementById(obj.oid);
            let rect = node.getBoundingClientRect();
            send_message({C: 'M', oid: obj.oid, x: rect.left, y: rect.top, w: rect.width, h: rect.height});
        } else if (obj.m === 'dm') {
            drag_mode_active = true;
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
