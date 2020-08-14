var main;

function start(new_local_id, new_tab_id) {
    let chunks = location.pathname.split('/');
    if (chunks.length === 2) {
        let app_name = chunks[1];
        let local_style = document.createElement('link');
        local_style.setAttribute('rel', 'stylesheet');
        local_style.setAttribute('href', `/css/${app_name}.local.css`)
        document.head.append(local_style);
    }

    let local_id = localStorage.getItem('local_id');
    if (!local_id){
        local_id = new_local_id;
        localStorage.setItem('local_id', local_id);
    }
    let tab_id = sessionStorage.getItem('tab_id');
    if (!tab_id) {
        tab_id = new_tab_id;
        sessionStorage.setItem('tab_id', tab_id);
    }
    main = new WSClient(`ws://${location.host}${location.pathname}/ws/${local_id}/${tab_id}`);
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
                let value;
                if (obj.t === 'number' || obj.t === 'time') value = node.valueAsNumber;
                else if (obj.t === 'date') value = node.valueAsDate;
                else value = node.value;
                send_message({C: 'V', oid: obj.l, value: value});
                break;
            }

            case 'dm':
                drag_mode_active = true;
                break;

            case 'log':
                console.log(obj.l);
                break;

            case 'rst':
                let root = root_node();
                let parent = root.parentElement;
                root.remove();
                OID.clear();
                root = document.createElement('div');
                root.id = 'display';
                parent.appendChild(root);
                drag_mode_active = false;
                reset_events();
                break;

            case 'app':
                document.location = obj.l;
                break;

            case 'title':
                document.title = obj.l;
                break;

            case 'valid':
                let node = OID.node(obj.l);
                send_message({C: 'VALID', oid: obj.l, validity: node.validity.valid});
        }
    }

    send_message({C: 'REFRESH'});
}

function send_message(message) {
    main.send(serializer.encode(message));
}

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

function process_bind_value(variable, oid, target) {
    let value;
    if (target.type === 'number') value = target.valueAsNumber;
    else if (target.type === 'time') {
        value = target.valueAsDate;
        //value.setMinutes(value.getMinutes() + value.getTimezoneOffset());
        value = value.getTime();
    }
    else if (target.type === 'date') {
        value = target.valueAsDate;
        //value.setMinutes(value.getMinutes() + value.getTimezoneOffset());
    }
    else value = target.value;
    send_message({C: 'B', v: variable, oid: oid, x: value})
}

function process_key(method, oid, key) {
    send_message({C: 'KEY', method: method, oid: oid, key: key});
}
