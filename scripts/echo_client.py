import asyncio
import logging
import websockets
from concurrent.futures import ThreadPoolExecutor
import pudb
import time


async def ainput(prompt=">>> "):
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)


async def reader(ws, prompt=">>> "):
    while True:
        data = await ainput(prompt)
        await ws.send(data)


async def client(uri):
    ws = await websockets.connect(uri, ping_interval=5)
    st = time.time()

    reader_rask = asyncio.create_task(reader(ws))

    try:
        async for msg in ws:
            print(msg)
    except Exception as e:
        et = time.time()
        print(f"Duration: {et - st}")
        raise e


if __name__ == "__main__":

    uri = input("websocket server uri [ws://192.168.4.1:7777]: ")
    if not uri:
        uri = "ws://192.168.4.1:7777"
    logger = logging.getLogger('websockets.client')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    loop = asyncio.new_event_loop()
    loop.run_until_complete(client(uri))
