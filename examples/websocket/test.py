import uasyncio as asyncio
from websockets.client import connect
# from websockets.server import serve


async def client_test():
    ws = await connect("wss://192.168.3.116:7777/test")
    if not ws:
        print("connection failed")
        return
    print("sending")
    await ws.send("This is a story")
    print("sent")
    async for msg in ws:
        print(msg)
    await ws.wait_closed()


async def add_client(ws, path):
    print("Connection on {}".format(path))

    try:
        await ws.send("adding client to {}".format(path))
        async for msg in ws:
            print(msg)
            await ws.send(msg)
    finally:
        print("Disconnected")


# ws_server = serve(add_client, "0.0.0.0", 7777)
# loop = asyncio.get_event_loop()
# loop.run_until_complete(ws_server)
# loop.run_forever()
