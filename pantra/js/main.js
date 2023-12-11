let main;

function start(new_local_id, new_tab_id, cache_id, web_path) {
    let chunks = location.pathname.split('/');
    let prefix_len = web_path.split('/').length - 1;
    if (chunks.length >= 2 + prefix_len) {
        let app_name = chunks[1 + prefix_len];
        let local_style = document.createElement('link');
        local_style.setAttribute('rel', 'stylesheet');
        local_style.setAttribute('href', `${web_path}/css/${app_name}.local.css?${cache_id}`);
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
    let protocol = location.protocol === "http:"? "ws" : "wss";
    main = new WSClient(`${protocol}://${location.host}${location.pathname}/ws/${local_id}/${tab_id}`);
    main.onrefresh = () => {
        send_message(Messages.up())
    };

    main.onmessage = (data) => {
        let obj = serializer.decode(data);
        process_message(obj);
    };

    send_message(Messages.refresh());
}

function send_message(message) {
    main.send(serializer.encode(message));
}

function process_click(method, oid) {
    send_message(Messages.click(method, oid));
}

function process_drag_start(method, oid, event) {
    send_message(Messages.drag_start(method, oid, event));
}

function process_drag_move(event) {
    send_message(Messages.drag_move(event));
}

function process_drag_stop(event) {
    send_message(Messages.drag_stop(event));
}

function process_select(method, oid, options) {
    let opts = Object.values(options).reduce((acc, cur) => {
        acc.push(OID.get(cur));
        return acc;
    }, []);
    send_message(Messages.select(method, oid, opts));
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
    else if (target.type === 'checkbox') {
        value = target.checked;
    }
    else value = target.value;
    send_message(Messages.bind_value(variable, oid, value))
}

function process_key(method, oid, key) {
    send_message(Messages.key(method, oid, key));
}

function process_call(oid, method) {
    send_message(Messages.call(oid, method, [...arguments].slice(2)));
}
