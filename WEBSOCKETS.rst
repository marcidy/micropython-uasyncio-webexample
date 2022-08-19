Micropython uasycio websockets
==============================
A client/server websockets implementation

Examples
--------
see http://github.com/marcidy/micropython-uasyncio-webexample for both the client and server in action and how to use them in web pages as well as with python `websockets`.  That repository also has unit tesets for the protocol.

protocol.py
-----------
The heart of the websocket is the protocol, developed by http://github.com/danni/uwebsockets.

The protocol has been updated to take fragmentation into account and checked against python `websocket` 10.3.

client.py
---------
`client.connect(uri)` creates a socket, connectes to `uri` and attempts to upgrade the connection to a WebSocket.  

The returned WebSocketClient should then be run as::

    ws = await websocket.client.connect('ws://server.tld:7777/path')

    async for msg in ws:
        print(msg)

server.py
---------
`server.connect(client_callback, host, port)` is run as a uasyncio task, which runs `uasyncio.start_server` with a modified first argument which
performs the server handshake and calls `client_callback` on the resulting WebSocket as `uasyncio.create_task(client_callback(ws, path))`

note: this call is not compatible with websockets 10.3 where `path` is an attribute on the websocket object.  A future update will address this.
