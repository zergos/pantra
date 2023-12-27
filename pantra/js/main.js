let wsConnection;

function start(newLocalId, newTabId, cacheId, webPath) {
    let chunks = location.pathname.split('/');
    let prefixLen = webPath.split('/').length - 1;
    if (chunks.length >= 2 + prefixLen) {
        let appName = chunks[1 + prefixLen];
        let localStyle = document.createElement('link');
        localStyle.setAttribute('rel', 'stylesheet');
        localStyle.setAttribute('href', `${webPath}/css/${appName}.local.css?${cacheId}`);
        document.head.append(localStyle);
    }

    let localId = localStorage.getItem('local_id');
    if (!localId){
        localId = newLocalId;
        localStorage.setItem('local_id', localId);
    }
    let tabId = sessionStorage.getItem('tab_id');
    if (!tabId) {
        tabId = newTabId;
        sessionStorage.setItem('tab_id', tabId);
    }
    let protocol = location.protocol === "http:"? "ws" : "wss";
    wsConnection = new WSClient(`${protocol}://${location.host}${location.pathname}/ws/${localId}/${tabId}${location.search}`);
    wsConnection.onrefresh = () => {
        sendMessage(Messages.up())
    };

    wsConnection.onmessage = (data) => {
        let obj = serializer.decode(data);
        process_message(obj);
    };

    sendMessage(Messages.refresh());
}

function sendMessage(message) {
    wsConnection.send(serializer.encode(message));
}

function processClick(method, oid) {
    sendMessage(Messages.click(method, oid));
}

function processDragStart(method, oid, event) {
    sendMessage(Messages.dragStart(method, oid, event));
}

function processDragMove(event) {
    sendMessage(Messages.dragMove(event));
}

function processDragStop(event) {
    sendMessage(Messages.dragStop(event));
}

function processSelect(method, oid, options) {
    let opts = Object.values(options).reduce((acc, cur) => {
        acc.push(OID.get(cur));
        return acc;
    }, []);
    sendMessage(Messages.select(method, oid, opts));
}

function processBindValue(variable, oid, target) {
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
    sendMessage(Messages.bindValue(variable, oid, value))
}

function process_key(method, oid, key) {
    sendMessage(Messages.key(method, oid, key));
}

function process_call(oid, method) {
    sendMessage(Messages.call(oid, method, [...arguments].slice(2)));
}
