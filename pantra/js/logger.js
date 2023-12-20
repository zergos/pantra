let _serializerDebug = false;
let _wsDebug = false;
let _protoDebug = false;

function getCurrentTimeFormatted() {
  const now = new Date();
  return now.toISOString();
}

function seLog(message) {
    if (_serializerDebug)
        console.log(`[${getCurrentTimeFormatted()}]: ${message}`);
}

function wsLog(message) {
    if (_wsDebug)
	    console.log(`[${getCurrentTimeFormatted()}] - WSClient: ${message}`)
}

function protoLog(message) {
    if (_protoDebug)
	    console.log(`[${getCurrentTimeFormatted()}] - Proto: ${message}`)
}
