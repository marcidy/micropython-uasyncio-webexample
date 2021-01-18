from websockets.client import connect
from websockets.server import serve
import uasyncio as asyncio


async def client_test():
    ws = await connect("ws://192.168.3.65:7777/test")
    if not ws:
        print("connection failed")
        return
    await ws.send("This is a story")
    print(await ws.recv())
    await ws.wait_closed()


async def add_client(ws, path):
    print("Connection on {}".format(path))

    try:
        async for msg in ws:
            print(msg)
            await ws.send(msg)
    finally:
        print("Disconnected")


ws_server = serve(add_client, "0.0.0.0", 7777)
loop = asyncio.get_event_loop()
loop.run_until_complete(ws_server)
loop.run_forever()
