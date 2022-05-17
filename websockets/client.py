"""
Websockets client for micropython

Directly based on
https://github.com/danni/uwebsockets

which is based very heavily off
https://github.com/aaugustin/websockets/blob/master/websockets/client.py

"""

import ubinascii as binascii
import urandom as random
import uasyncio as asyncio
from .protocol import Websocket, urlparse


class WebsocketClient(Websocket):
    is_client = True


async def connect(uri):
    """
    Connect a websocket.
    """

    print("client connect")
    uri = urlparse(uri)
    ss, _ = await asyncio.open_connection(uri.hostname, uri.port)

    if uri.proto == "wss":
        print("trying ssl")
        import ssl
        ssl_sock = ssl.wrap_socket(ss.s)
        ss.s = ssl_sock

    def send_header(header, *args):
        ss.write(header % args + '\r\n')

    # Sec-WebSocket-Key is 16 bytes of random base64 encoded
    key = binascii.b2a_base64(bytes(random.getrandbits(8)
                                    for _ in range(16)))[:-1]

    print("sending headers")
    send_header(b'GET %s HTTP/1.1', uri.path or '/')
    await ss.drain()
    send_header(b'Host: %s:%s', uri.hostname, uri.port)
    await ss.drain()
    send_header(b'Connection: Upgrade')
    await ss.drain()
    send_header(b'Upgrade: websocket')
    await ss.drain()
    send_header(b'Sec-WebSocket-Key: %s', key)
    await ss.drain()
    send_header(b'Sec-WebSocket-Version: 13')
    await ss.drain()
    send_header(b'Origin: http://localhost')
    await ss.drain()
    send_header(b'')

    await ss.drain()

    header = (await ss.readline())[:-2]
    if not header.startswith(b'HTTP/1.1 101 '):
        return False
        # probably need to skip or something?

    # We don't (currently) need these headers
    # FIXME: should we check the return key?
    if uri.proto == "wss":
        return WebsocketClient(ss)

    while header:
        header = await ss.readline()
        if header == b"\r\n":
            break

    return WebsocketClient(ss)
