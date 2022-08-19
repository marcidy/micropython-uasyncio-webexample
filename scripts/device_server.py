import time
import pathlib
import logging
import logging.handlers
import asyncio
from collections import defaultdict
import json
import ssl
import websockets


def log_setup():
    handler = logging.handlers.TimedRotatingFileHandler(
        "device_server.log", when='D')
    formatter = logging.Formatter(
        '%(asctime)s device_server [%(process)d]: %(message)s',
        '%b %d %H:%M:%S')
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


devices = {}
pages = defaultdict(set)


async def add_page(websocket, path):
    print(f"Page connected to {path}")
    pages[path].add(websocket)
    try:
        async for msg in websocket:
            logging.info( "< " + path + "/ " + msg)
            if path in devices:
                await devices[path].send(msg)
    finally:
        pages[path].remove(websocket)
        print("Page Left")


async def add_device(websocket, path):
    print(f"Device connected: {path}")
    if path in devices:
        ws = devices.pop(path)
        await ws.close()
    devices[path] = websocket

    try:
        async for msg in websocket:
            logging.info("> " + path + "/ " + msg)
            if len(pages[path]) > 0:
                asyncio.gather(*[pg.send(msg) for pg in pages[path]])
    finally:
        if path in devices:
            devices.pop(path)
        await websocket.close()


page_server = websockets.serve(
    add_page, '127.0.0.1', 7771,
    compression=None,
    ping_interval=None,
    ping_timeout=None)


device_server = websockets.serve(
    add_device, '0.0.0.0', 7770,
    compression=None,
    ping_interval=None,
    ping_timeout=None)


if __name__ == "__main__":
    log_setup()
    logging.info('Device Server restarted')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(device_server)
    loop.run_until_complete(page_server)
    loop.run_forever()
