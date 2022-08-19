import sys
sys.path.insert(0, "..")  # shadow official websockets

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
from .utils import Stream


def print_frame(frame):
    print("")
    for i, b in enumerate(frame):
        if ((i+1) % 4) != 0:
            print(f"{b:08b} ", end="")
        else:
            print(f"{b:08b}")


# class Stream:
#     ''' Mimics an uasyncio.stream.Stream which underlies websockets'''
#     def __init__(self,
#                  read_buf=b'',
#                  write_buf=b'',
#                  throw=None,
#                  throw_on_byte=0,
#                  ):
#         self.read_buf = read_buf
#         self.write_buf = write_buf
#         self.sent_buf = b''
#         self.throw_on_byte = throw_on_byte
#         self.throw = throw
#         self.bytes_read = 0
#
#     async def readexactly(self, n):
#         if self.throw:
#             if (self.bytes_read + n >= self.throw_on_byte):
#                 raise self.throw
#
#         if n > len(self.read_buf):
#             raise ValueError
#
#         out = self.read_buf[0:n]
#         self.read_buf = self.read_buf[n:]
#         return out
#
#     async def drain(self):
#         self.sent_buf += self.write_buf
#         self.write_buf = b''
#
#     def write(self, in_buf):
#         self.write_buf += in_buf
#
#     async def wait_closed(self):
#         if self.throw:
#             raise self.throw


def test_urlparse():
    # Note: Shouldn't site.tld:port, site.tld, and site.tld/ all have the path
    # "/"?
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


@pytest.mark.asyncio
async def test_websocket_write_client_text():
    in_buf = bytes([0x81, 0x05, 0x48, 0x65, 0x6c, 0x6c, 0x6f])

    s = Stream()
    ws = Websocket(s)

    await ws.send('Hello')
    assert s.sent_buf == in_buf


@pytest.mark.asyncio
async def test_websocket_write_client_bytes():
    out_buf = bytes([0x82, 0x05, 0x48, 0x65, 0x6c, 0x6c, 0x6f])

    s = Stream()
    ws = Websocket(s)

    await ws.send(b'Hello')
    assert s.sent_buf == out_buf


@pytest.mark.asyncio
@patch('websockets.protocol.random')
async def test_websocket_write_masked(random):

    # mask uses random bits, but we aren't testing random, just masking
    fin = 0x80
    not_rand = int(b'A55AE8E8', 16)
    masked = 0x80
    length = 0x05
    mask = not_rand.to_bytes(4, 'big')
    def getrandbits(x):
        if x == 32:
            return not_rand
        else:
            raise ValueError()

    random.getrandbits = getrandbits

    # expectation
    out_buf = bytes([
        fin | OP_TEXT,
        masked | length,
        *mask,
        0xED, 0x3F, 0x84, 0x84, 0xCA # masked Hello
    ])
    s = Stream()
    ws = Websocket(s)
    ws.is_client = True  # client triggers masking

    await ws.send('Hello')

    assert s.sent_buf == out_buf


@pytest.mark.asyncio
async def test_websocket_write_magic_lenght_126():
    in_data = b'f'*255
    fin = 0x80
    opcode = OP_BYTES
    mask = 0x00
    actual_length = len(in_data).to_bytes(2, 'big')

    out_buf = bytes([
        fin | opcode,
        mask | 126,
        *actual_length,
        *in_data,
    ])

    s = Stream()
    ws = Websocket(s)

    await ws.send(in_data)

    assert s.sent_buf == out_buf


@pytest.mark.asyncio
async def test_websocket_write_magic_length_127():
    in_data = "x" * 70000
    fin = 0x80
    opcode = OP_TEXT
    mask = 0x00
    actual_length = len(in_data).to_bytes(8, 'big')

    out_buf = bytes([
        fin | opcode,
        mask | 127,
        *actual_length,
        *(in_data.encode('utf-8')),
    ])

    s = Stream()
    ws = Websocket(s)

    await ws.send(in_data)

    assert s.sent_buf == out_buf


# Websocket.protocol.recv are very similar to read_frame based testcases


@pytest.mark.asyncio
async def test_websocket_recv_text():
    fin = 0x80
    opcode = OP_TEXT
    mask = 0x00
    in_data = b'Hello'
    length = len(in_data)

    buf = bytes([
        fin | opcode,
        mask | length,
        *in_data,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    data = await ws.recv()

    assert data == in_data.decode('utf-8')


@pytest.mark.asyncio
async def test_websocket_recv_bytes():
    fin = 0x80
    opcode = OP_BYTES
    mask = 0x00
    in_data = b'Hello'
    length = len(in_data)

    buf = bytes([
        fin | opcode,
        mask | length,
        *in_data,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    data = await ws.recv()

    assert data == in_data


@pytest.mark.asyncio
async def test_websocket_recv_close():
    fin = 0x80
    opcode = OP_CLOSE
    mask = 0x00
    length = 0

    buf = bytes([
        fin | opcode,
        mask | length,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    data = await ws.recv()

    assert not ws.open
    assert s.sent_buf == b'\x88\x02\x03\xe8'


@pytest.mark.asyncio
async def test_websocket_recv_ping():
    fin = 0x80
    opcode = OP_PING
    mask = 0x00
    in_data = b'weeeeee'
    length = len(in_data)

    buf = bytes([
        fin | opcode,
        mask | length,
        *in_data,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    data = await ws.recv()

    assert s.sent_buf == bytes([
        0x80 | OP_PONG,
        mask | length,
        *in_data])


@pytest.mark.asyncio
async def test_websocket_recv_pong():
    ''' testing recv doesn't raise, PONGs have no real reqs'''
    fin = 0x80
    opcode = OP_PONG
    mask = 0x00
    in_data = b'whatever'
    length = len(in_data)

    buf = bytes([
        fin | opcode,
        mask | length,
        *in_data,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    await ws.recv()


@pytest.mark.asyncio
async def test_websocket_recv_cont():
    fin1 = 0x00
    opcode1 = OP_TEXT
    mask1 = 0x00
    in_data1 = b"I'm a cont"
    length1 = len(in_data1)

    fin2 = 0x80
    opcode2 = OP_CONT
    mask2 = 0x00
    in_data2 = b"inuation frame"
    length2 = len(in_data2)

    buf = bytes([
        fin1 | opcode1,
        mask1 | length1,
        *in_data1,
        fin2 | opcode2,
        mask2 | length2,
        *in_data2,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    out = await ws.recv()

    assert out == (in_data1 + in_data2).decode('utf-8')


@pytest.mark.asyncio
async def test_websocket_raises_on_bad_opcode():
    fin = 0x80
    opcode = 255
    mask = 0x00
    in_data = b'blah'
    length = len(in_data)

    buf = bytes([
        fin | opcode,
        mask | length,
        *in_data,
    ])

    s = Stream(buf)
    ws = Websocket(s)

    with pytest.raises(ValueError) as exc_info:
        await ws.recv()

        assert exc_info.value.args[0] == opcode


@pytest.mark.asyncio
async def test_websocket_asyncio_interfaces():
    test_msgs = [
        'hello',
        'how are you',
        'find thanks',
        'goodbye']

    s = Stream()
    ws = Websocket(s)
    # borrow send ot create frames for messages
    for msg in test_msgs:
        await ws.send(msg)

    s.read_buf, s.sent_buf = s.sent_buf, b''

    out = []

    async for msg in ws:
        out.append(msg)

    assert out == test_msgs

@pytest.mark.asyncio
async def test_websocket_context_manager_interface():
    test_msgs = [
        'hello',
        'how are you',
        'find thanks',
        'goodbye']

    s = Stream()
    ws = Websocket(s)

    for msg in test_msgs:
        await ws.send(msg)

    s.read_buf, s.sent_buf = s.sent_buf, b''
    out = []

    with ws as f:
        async for msg in ws:
            out.append(msg)

    assert not ws.open
    assert test_msgs == out


@pytest.mark.asyncio
async def test_websocket_send_wrong_object():
    o = object()
    s = Stream()
    ws = Websocket(s)

    with pytest.raises(TypeError):
        await ws.send(o)

