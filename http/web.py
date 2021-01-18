import gc
import re
import os


url_pat = re.compile(
    r'^(([^:/\\?#]+):)?' +  # scheme                # NOQA
    r'(//([^/\\?#]*))?' +   # user:pass@host:port   # NOQA
    r'([^\\?#]*)' +         # route                 # NOQA
    r'(\\?([^#]*))?' +      # query                 # NOQA
    r'(#(.*))?')            # fragment              # NOQA


def route(file):

    async def _func(writer):
        await send_file(writer, file)

    return _func


async def send_file(writer, file):
    fstat = os.stat(file)
    fsize = fstat[6]

    writer.write(b'HTTP/1.0 200 OK\r\n')
    writer.write(b'Content-Type: text/html\r\n')
    writer.write('Content-Length: {}\r\n'.format(fsize).encode('utf-8'))
    writer.write(b'Accept-Ranges: none\r\n')
    writer.write(b'Transfer-Encoding: chunked\r\n')
    writer.write(b'\r\n')
    await writer.drain()
    gc.collect()
    max_chunk_size = 1024
    with open(file, 'rb') as f:
        for x in range(0, fsize, max_chunk_size):
            chunk_size = min(max_chunk_size, fsize-x)
            chunk_header = "{:x}\r\n".format(chunk_size).encode('utf-8')
            writer.write(chunk_header)
            writer.write(f.read(chunk_size))
            writer.write(b'\r\n')
            await writer.drain()
            gc.collect()
    writer.write(b"\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    gc.collect()


routes = {
    b'/': route('/www/page.htm'),
    b'/static/jquery.js': route('/www/jquery-3.5.1.min.js')}


async def server(reader, writer):
    req = await reader.readline()
    print(req)
    method, uri, proto = req.split(b" ")
    m = re.match(url_pat, uri)
    route = m.group(5)

    while True:
        h = await reader.readline()
        if h == b"" or h == b"\r\n":
            break
        print(h)

    print("route: {}".format(route.decode('utf-8')))
    test = route in routes
    print("Route found?: {}".format(test))

    if route in routes:
        await routes[route](writer)
    else:
        writer.write(b'HTTP/1.0 404 Not Found\r\n')
        writer.write(b'\r\n')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    gc.collect()
