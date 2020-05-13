class WSClient {
	constructor(url) {
		this.url = url;
		this.autoReconnectInterval = 5*1000;
		this.connected = false;
	}
	refresh(callback=null) {
		if (!this.connected) {
			if (callback)
				this.callback = callback;
			this.instance = new WebSocket(this.url);
			this.instance.binaryType = "arraybuffer";
			this.instance.onopen = () => this.onopen();
			this.instance.onmessage = (message) => this.onmessage(message.data);
			this.instance.onerror = () => this.onerror();
			this.instance.onclose = () => this.onclose();
		}
	}
	reconnect() {
		this.connected = false;
		console.log(`WSClient: retry in ${this.autoReconnectInterval}ms`);
		//this.instance.removeAllListeners();
		setTimeout(this.refresh, this.autoReconnectInterval);
	}
	onopen() {
		console.log(`WSClient: connected`);
		this.connected = true;
		this.callback();
	}
	onclose() {
		console.log('WSClient: closed');
		this.connected = false;
	}
	onerror(e) {
		this.connected = false;
		console.log(`WSClient: error ${e} : ${e.code}`);
		if (e.code === 'ECONNREFUSED')
			this.reconnect(e);
	}
	onmessage(data) {
		console.log('message coming ' + data);
	}
	send(data, option) {
		if (!this.connected) {
			this.refresh(() => this.send(data, option));
			return;
		}
		try {
			this.instance.send(data, option);
		} catch (e) {
			this.onerror(e);
		}
	}
}

