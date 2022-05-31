import sys
sys.path.insert(0, "../")  # shadow official websockets

from unittest.mock import patch
import pytest
from websockets.protocol import(
    urlparse,
    Websocket,
    OP_CONT,
    OP_TEXT,
    OP_BYTES,
    OP_CLOSE,
    OP_PING,
    OP_PONG,
)


def print_frame(frame):
    print("")
    for i, b in enumerate(frame):
        if ((i+1) % 4) != 0:
            print(f"{b:08b} ", end="")
        else:
            print(f"{b:08b}")


def test_urlparse():
    tcs = (
        (
            "ws://localhost",
            ("ws", "localhost", 80, None)
        ),
        (
            "ws://localhost.com:12345/",
            ("ws", "localhost.com", 12345, None)
        ),
        (
            "wss://localhost.com:12345/test",
            ("wss", "localhost.com", 12345, "/test")
        ),
    )

    for tc, result in tcs:
        uri = urlparse(tc)

        assert uri.proto == result[0]
        assert uri.hostname == result[1]
        assert uri.port == result[2]
        assert uri.path == result[3]


class Stream:
    def __init__(self,
                 read_buf=b'',
                 write_buf=b'',
                 throw=None,
                 throw_on_byte=0,
                 ):
        self.read_buf = read_buf
        self.write_buf = write_buf
        self.throw_on_byte = throw_on_byte
        self.throw = throw
        self.bytes_read = 0

    async def readexactly(self, n):
        if self.throw:
            if (self.bytes_read + n >= self.throw_on_byte):
                raise self.throw

        if n > len(self.read_buf):
            raise ValueError

        out = self.read_buf[0:n]
        self.read_buf = self.read_buf[n:]
        return out

    async def drain(self):
        self.write_buf = b''

    def write(self, in_buf):
        self.write_buf += in_buf

    async def wait_closed(self):
        if self.throw:
            raise self.throw


def test_websocket_create():
    s = Stream()
    ws = Websocket(s)

    assert ws.open
    assert not ws.fragment
    assert ws._stream == s


@pytest.mark.asyncio
async def test_websocket_read():
    fin = 0x80
    opcode = OP_TEXT
    mask = 0x00
    in_data = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05]
    length = len(in_data)

    buf = bytes([
        fin | opcode,
        mask | length,
        *in_data
    ])

    s = Stream(buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == 0x01
    assert data == bytes(in_data)
    assert not len(s.read_buf)


@pytest.mark.asyncio
async def test_websocket_masked_hello():
    fin = 0x80
    opcode = OP_TEXT
    mask = 0x80
    mask_data = b"\x00\x00\x00\x00"
    in_data = b"Hello!"
    length = len(in_data)

    in_buf = bytes([
        fin | opcode,
        mask | length,
        *mask_data,
        *in_data
    ])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_TEXT
    assert data == b"Hello!"


@pytest.mark.asyncio
async def test_websocket_magic_length_126():
    ''' Extended payload length case 126, with an ineffective mask (0000) '''
    fin = 0x80
    opcode = OP_TEXT
    mask = 0x80
    mask_data = b'\x00' * 4
    magic_length = 126
    in_data = b"g" * 255 # need this in 2 bytes, network byte order
    actual_length = len(in_data).to_bytes(2, 'big')

    in_buf = bytes([
        fin | opcode,
        mask | magic_length,
        *actual_length,
        *mask_data,
        *in_data
    ])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_TEXT
    assert data == in_data


@pytest.mark.asyncio
async def test_websocket_magic_length_127():
    '''Extended payload length contniued without mask'''
    fin = 0x80
    opcode = OP_BYTES
    mask = 0x00
    magic_length = 127
    in_data = b"\x0c" * 1024
    actual_length = len(in_data).to_bytes(8, 'big')

    in_buf = bytes([
        fin | opcode,
        mask | magic_length,
        *actual_length,
        *in_data,
    ])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_BYTES
    assert data == in_data


# Examples from IETF RFC 6455 sec 5.7

@pytest.mark.asyncio
async def test_websocket_single_frame_unmasked_text_message():
    in_buf = bytes([0x81, 0x05, 0x48, 0x65, 0x6c, 0x6c, 0x6f])
    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_TEXT
    assert data == b"Hello"


@pytest.mark.asyncio
async def test_websocket_single_frame_masked_test_message():
    in_buf = bytes([
        0x81, 0x85, 0x37, 0xfa, 0x21, 0x3d, 0x7f, 0x9f, 0x4d, 0x51, 0x58
    ])
    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_TEXT
    assert data == b"Hello"


@pytest.mark.asyncio
async def test_websocket_fragmented_unmasked_text_message():
    in_buf1 = bytes([ 0x01, 0x03, 0x48, 0x65, 0x6c ])
    in_buf2 = bytes([ 0x80, 0x02, 0x6c, 0x6f ])

    s = Stream(in_buf1)
    ws = Websocket(s)

    fin1, opcode1, data1 = await ws.read_frame()
    s.read_buf = in_buf2
    fin2, opcode2, data2 = await ws.read_frame()

    assert not fin1
    assert opcode1 == OP_TEXT
    assert data1 == b'Hel'
    assert fin2
    assert opcode2 == OP_CONT
    assert data2 == b'lo'


@pytest.mark.asyncio
async def test_websocket_ping_request():
    ''' Note this won't send a pong, just testing the input side '''
    in_buf = bytes([ 0x89, 0x05, 0x48, 0x65, 0x6c, 0x6c, 0x6f ])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert OP_PING
    assert data == b"Hello"

    in_buf =  bytes([
        0x8a, 0x85, 0x37, 0xfa, 0x21, 0x3d, 0x7f, 0x9f, 0x4d, 0x51, 0x58, ])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert OP_PING
    assert data == b"Hello"


@pytest.mark.asyncio
async def test_websocket_long_binary_message():
    in_data = b"\x01" * 256
    in_buf = bytes([0x82, 0x7e, 0x01, 0x00, *in_data])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_BYTES
    assert data == in_data


@pytest.mark.asyncio
async def test_websocket_really_long_binary_message():
    in_data = b"\xA5" * 65536
    in_buf = bytes([
        0x82, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
        *in_data
    ])

    s = Stream(in_buf)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_BYTES
    assert data == in_data


@pytest.mark.asyncio
async def test_websocket_throw_memory_error_in_read_frame():
    in_buf = bytes([
        0x81, 0x85, 0x37, 0xfa, 0x21, 0x3d, 0x7f, 0x9f, 0x4d, 0x51, 0x58
    ])

    s = Stream(in_buf, throw=MemoryError, throw_on_byte=5)
    ws = Websocket(s)

    fin, opcode, data = await ws.read_frame()

    assert fin
    assert opcode == OP_CLOSE
    assert not data


@pytest.mark.asyncio
async def test_websocket_throw_other_error_in_read_frame():
    in_buf = bytes([
        0x81, 0x85, 0x37, 0xfa, 0x21, 0x3d, 0x7f, 0x9f, 0x4d, 0x51, 0x58
    ])

    s = Stream(in_buf, throw=ValueError)
    ws = Websocket(s)

    with pytest.raises(ValueError):
        fin, opcode, data = await ws.read_frame()
