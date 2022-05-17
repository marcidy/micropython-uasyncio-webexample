import ubinascii as binascii
import uhashlib as hashlib
import uasyncio
from uasyncio import StreamReader as Stream
import gc
import re
from .server import connect

try:
    import usocket as socket
except:
    import socket

import ussl as ssl
# from .key import key as k1
# from .cert import cert as c1

cert = ""
with open("/certs/cert.pem", 'rb') as f:
    cert = f.read()

key = ""
with open("/certs/key.pem", 'rb') as f:
    key = f.read()

# key = binascii.unhexlify(k1)
# cert = binascii.unhexlify(c1)


class SSLServer:

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.close()
        await self.wait_closed()

    def close(self):
        self.task.cancel()

    async def wait_closed(self):
        await self.task

    async def _serve(self, s, cb):
        global key
        global cert
        while True:
            try:
                yield uasyncio.core._io_queue.queue_read(s)
            except uasyncio.core.CancelledError:
                s.close()
                return

            try:
                s2, addr = s.accept()
            except Exception:
                continue
            print("conn from: {}".format(addr))
            s2 = ssl.wrap_socket(s2, server_side=True, key=key, cert=cert)
            print(s2)
            s2.setblocking(False)
            s2s = Stream(s2, {"peername": addr})
            uasyncio.core.create_task(cb(s2s, s2s))
            key = None
            cert = None
            gc.collect()


async def start_server(cb, host, port, backlog=5):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host = socket.getaddrinfo(host, port)[0]
    print("host: {}".format(host))
    s.setblocking(False)
    s.bind(host[-1])
    s.listen(backlog)

    srv = SSLServer()
    srv.task = uasyncio.core.create_task(srv._serve(s, cb))
    return srv

async def serve(cb, host, port):

    async def _connect(reader, writer):
        await connect(reader, writer, cb)

    return await start_server(_connect, host, port)
