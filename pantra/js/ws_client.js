let CONNECT_INTERVALS = [5,5,5,5,10,20,30,60,120,300,600];

function showOnlineBar() {
	let bar = document.getElementById('online-bar');
	bar.removeAttribute('style');
}

function hideOnlineBar() {
	let bar = document.getElementById('online-bar');
	bar.setAttribute('style', 'display: none');
}

class WSClient {
	constructor(url) {
		this.url = url;
		this.currentInterval = -1;
		this.connected = false;
		this.init = false;
		this.want_refresh = false;
	}
	refresh(callback=null) {
		if (!this.connected) {
			this.callback = callback;
			this.ws = new WebSocket(this.url);
			this.ws.binaryType = "arraybuffer";
			this.ws.onopen = () => this.onopen();
			this.ws.onmessage = (message) => this.onmessage(message.data);
			this.ws.onclose = (e) => this.onclose(e);
		}
	}
	reconnect() {
		this.connected = false;
		if (this.currentInterval >= CONNECT_INTERVALS.length) {
			wsLog("no more retries, I gave up");
			return;
		}
		let autoReconnectInterval = CONNECT_INTERVALS[this.currentInterval] * 1000;
		wsLog(`retry in ${autoReconnectInterval/1000}s`);
		//this.instance.removeAllListeners();
		setTimeout(() => this.refresh(), autoReconnectInterval);
	}

	reopen() {
		this.want_refresh = true;
		this.ws.close(1000);
	}

	onrefresh() {
		wsLog('refreshing connection')
	}
	onopen() {
		wsLog('connected');
		this.connected = true;
		this.currentInterval = 0;
		showOnlineBar();
		if (this.init)
			this.onrefresh();
		else
			this.init = true;
		if (this.callback)
			this.callback();
	}
	onclose(e) {
		this.connected = false;
		hideOnlineBar();
		switch (e.code) {
			case 1006:
				wsLog('server down...');
				this.currentInterval ++;
				this.reconnect();
				break;
			case 1000:
				wsLog('connection suspended');
				if (this.want_refresh) {
					this.want_refresh = false;
					this.refresh();
				}
				break;
			default:
				wsLog(`unrecoverable error ${e.code}`);
		}
	}
	onmessage(data) {
		wsLog(`message coming ${data}`);
	}
	send(data, option) {
		if (!this.connected) {
			this.refresh(() => this.send(data, option));
			return;
		}
		try {
			this.ws.send(data, option);
		} catch (e) {
			this.onerror(e);
		}
	}
}

