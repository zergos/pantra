function getCurrentTimeFormatted() {
  const now = new Date();
  return now.toISOString();
}

function seLog(message) {
    if (config.JS_SERIALIZER_LOGGING)
        console.log(`[${getCurrentTimeFormatted()}]: ${message}`);
}

function wsLog(message) {
    if (config.JS_WS_LOGGING)
	    console.log(`[${getCurrentTimeFormatted()}] - WSClient: ${message}`)
}

function protoLog(message) {
    if (config.JS_PROTO_LOGGING)
	    console.log(`[${getCurrentTimeFormatted()}] - Proto: ${message}`)
}
