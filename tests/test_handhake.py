import sys
sys.path.insert(0, "..") # shadow websockets from [v]env

from unittest.mock import patch, MagicMock
import pytest
from websockets.client import connect as client_connect
from websockets.server import (
    serve,
    make_respkey,
    connect as server_connect,
)
from websockets.protocol import Websocket
from .utils import Stream


@pytest.mark.asyncio
@patch('websockets.client.random')
@patch('websockets.client.asyncio')
async def test_websockets_client_connect(asio, random):

    def getrandbits(x):
        return 0xA0

    random.getrandbits = getrandbits

    respkey = b"poops"

    server = "thisisnotreal.tld:12345"
    path = "weeeee"

    handshake = (
        b"HTTP/1.1 101 Switching Protocols\r\n"
        b"Upgrade: websocket\r\n"
        b"Connection: Upgrade\r\n"
        b"Sec-WebSocket-Accept: " + respkey + b"\r\n"
        b"Server: Micropython\r\n"
        b"\r\n"
    )

    response = (
        f"GET /{path} HTTP/1.1\r\n".encode('utf-8') +
        f"Host: {server}\r\n".encode('utf-8') +
        b"Connection: Upgrade\r\n"
        b"Upgrade: websocket\r\n"
        b"Sec-WebSocket-Key: oKCgoKCgoKCgoKCgoKCgoA==\r\n"
        b"Sec-WebSocket-Version: 13\r\n"
        b"Origin: http://localhost\r\n"
        b"\r\n"
    )

    s = Stream(handshake)

    async def gen_stream(a, b):
        return (s, s)

    asio.open_connection =  gen_stream

    ws = await client_connect(f"ws://{server}/{path}")

    assert ws.is_client
    assert s.sent_buf == response


@pytest.mark.asyncio
@patch('websockets.client.random')
async def test_websockets_server_handshake(random):

    def getrandbits(x):
        return 0xA0

    random.getrandbits = getrandbits
    path = "psyche"
    server = "whateveriwant.neato"

    handshake = (
        f"GET /{path} HTTP/1.1\r\n".encode('utf-8') +
        f"Host: {server}\r\n".encode('utf-8') +
        b"Connection: Upgrade\r\n"
        b"Upgrade: websocket\r\n"
        b"Sec-WebSocket-Key: oKCgoKCgoKCgoKCgoKCgoA==\r\n"
        b"Sec-WebSocket-Version: 13\r\n"
        b"Origin: http://localhost\r\n"
        b"\r\n"
    )

    response = (
        b"HTTP/1.1 101 Switching Protocols\r\n"
        b"Upgrade: websocket\r\n"
        b"Connection: Upgrade\r\n"
        b"Sec-WebSocket-Accept: L6fPoOJVlqyp7GKQkh0bqGA3nGw=\r\n"
        b"Server: Micropython\r\n"
        b"\r\n"
    )
    s = Stream(handshake)

    async def on_connect(ws, path):
        pass

    await server_connect(s, s, on_connect)

    assert s.sent_buf == response


@pytest.mark.asyncio
@patch('websockets.client.random')
@patch('websockets.client.asyncio')
async def test_websocket_server_nokey(asio, random):

    def getrandbits(x):
        return 0xA0

    random.getrandbits = getrandbits

    server = "thisisnotreal.tld:12345"
    path = "path"

    handshake = (
        f"GET /{path} HTTP/1.1\r\n".encode('utf-8') +
        f"Host: {server}\r\n".encode('utf-8') +
        b"Connection: Upgrade\r\n"
        b"Upgrade: websocket\r\n"
        b"Sec-WebSocket-Version: 13\r\n"
        b"Origin: http://localhost\r\n"
        b"\r\n"
    )

    s = Stream(handshake)

    async def on_connect(ws, path):
        pass

    await server_connect(s, s, on_connect)

    assert s.closed
    assert s.did_wait_closed


@pytest.mark.skip("donno how to test that 3 line function lmao, pls hlp")
@pytest.mark.asyncio
async def test_websocket_server_serve():

    out = {}

    async def on_connect(ws, path):
        out['ws'] = ws
        out['path'] = path

    host = "localhost"
    port = 9878
    path = "whatever"

    await serve(on_connect, host, port)

    s = Stream()
    async def gen_stream(a, b):
        return (s, s)

    wsc = await client_connect(f"ws://{host}:{port}/{path}")
