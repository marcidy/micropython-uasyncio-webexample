class Stream:
    ''' Mimics an uasyncio.stream.Stream which underlies websockets'''
    def __init__(self,
                 read_buf=b'',
                 write_buf=b'',
                 throw=None,
                 throw_on_byte=0,
                 ):
        self.read_buf = read_buf
        self.write_buf = write_buf
        self.sent_buf = b''
        self.throw_on_byte = throw_on_byte
        self.throw = throw
        self.bytes_read = 0
        self.closed = False
        self.did_wait_closed = False

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
        self.sent_buf += self.write_buf
        self.write_buf = b''

    def write(self, in_buf):
        self.write_buf += in_buf

    async def wait_closed(self):
        self.did_wait_closed = True
        if self.throw:
            raise self.throw

    async def readline(self):
        if (x :=self.read_buf.find(b"\r\n")) > -1:
            out, self.read_buf = self.read_buf[0:x+2], self.read_buf[x+2:]
            return out
        else:
            return b''

    def close(self):
        self.closed = True
