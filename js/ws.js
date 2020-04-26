var ws = new WebSocketClient();
ws.open(`ws://${hostname}/ws`);

ws.onopen = function (event) {
    let message = {Command: 'RESTART'};
    ws.send(serializer.encode(message));
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
        }
    };
    fileReader.readAsArrayBuffer(received_msg);
};

function process_click(method, oid) {
    let message = {Command: 'CLICK', Data: {method: method, oid: oid}};
    ws.send(serializer.encode(message));
}
