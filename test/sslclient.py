import logging
import asyncio
import websockets
import json


async def hello():
    uri = "wss://192.168.3.116:7777/TESTABC"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(['GET', 'wifi', [""]]))
        async for msg in websocket:
            print(msg)


logger = logging.getLogger('websockets.client')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
loop = asyncio.get_event_loop()
loop.run_until_complete(hello())
