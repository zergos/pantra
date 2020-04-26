// source file from https://github.com/websockets/ws/wiki/Websocket-client-implementation-for-auto-reconnect

function WebSocketClient(){
	this.number = 0;	// Message number
	this.autoReconnectInterval = 5*1000;	// ms
}
WebSocketClient.prototype.open = function(url){
	let that = this;
	this.url = url;
	this.instance = new WebSocket(this.url);
	this.instance.onopen = function () {
		that.onopen();
	};
	this.instance.onmessage = function(data,flags) {
		that.number ++;
		that.onmessage(data,flags,that.number);
	};
	this.instance.onclose = function(e) {
		switch (e.code){
		case 1000:	// CLOSE_NORMAL
			console.log("WebSocket: closed");
			break;
		default:	// Abnormal closure
			that.reconnect(e);
			break;
		}
		that.onclose(e);
	};
	this.instance.onerror = function(e) {
		switch (e.code){
		case 'ECONNREFUSED':
			that.reconnect(e);
			break;
		default:
			that.onerror(e);
			break;
		}
	};
}
WebSocketClient.prototype.send = function(data,option){
	try{
		this.instance.send(data,option);
	}catch (e){
		this.instance.emit('error',e);
	}
}
WebSocketClient.prototype.reconnect = function(e){
	console.log(`WebSocketClient: retry in ${this.autoReconnectInterval}ms`,e);
	//this.instance.removeAllListeners();
	let that = this;
	setTimeout(function(){
		console.log("WebSocketClient: reconnecting...");
		that.open(that.url);
	},this.autoReconnectInterval);
}
WebSocketClient.prototype.onopen = function(e){	console.log("WebSocketClient: open",arguments);	}
WebSocketClient.prototype.onmessage = function(data,flags,number){	console.log("WebSocketClient: message",arguments);	}
WebSocketClient.prototype.onerror = function(e){	console.log("WebSocketClient: error",arguments);	}
WebSocketClient.prototype.onclose = function(e){	console.log("WebSocketClient: closed",arguments);	}
