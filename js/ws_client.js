class WSClient {
	constructor(url) {
		this.url = url;
		this.autoReconnectInterval = 5*1000;
		this.connected = false;
		this.init = false;
		this.show_logs = false;
	}
	refresh(callback=null) {
		if (!this.connected) {
			this.callback = callback;
			this.instance = new WebSocket(this.url);
			this.instance.binaryType = "arraybuffer";
			this.instance.onopen = () => this.onopen();
			this.instance.onmessage = (message) => this.onmessage(message.data);
			this.instance.onerror = (e) => this.onerror(e);
			this.instance.onclose = (e) => this.onclose(e);
		}
	}
	reconnect() {
		this.connected = false;
		console.log(`WSClient: retry in ${this.autoReconnectInterval/1000}s`);
		//this.instance.removeAllListeners();
		setTimeout(() => this.refresh(), this.autoReconnectInterval);
	}
	onrefresh() {
		console.log('refreshing connection')
	}
	onopen() {
		if (this.show_logs)
			console.log(`WSClient: connected`);
		this.connected = true;
		if (this.init)
			this.onrefresh();
		else
			this.init = true;
		if (this.callback)
			this.callback();
	}
	onclose(e) {
		this.connected = false;
		switch (e.code) {
			case 1006:
				console.log(`WSClient: server down...`);
				this.reconnect();
				break;
			case 1000:
				if (this.show_logs)
					console.log('WSClient: connection suspended');
				break;
			default:
				console.error(`WSClient: unrecoverable error ${e.code}`);
		}
	}
	onerror(e) {
		this.connected = false;
		this.refresh();
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

