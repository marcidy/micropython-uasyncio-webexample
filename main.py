import uasyncio as asyncio
from websockets import client


async def reader(ws):
    print("reader")
    while True:
        async for msg in ws:
            print(msg)


async def writer(ws):
    print("writer")
    while True:
        ws.send("This is a test")
        await asyncio.sleep(1)


async def main():
    ws = await client.connect("wss://sharkparty.local:7777/TS001")
    asyncio.create_task(reader(ws))
    asyncio.create_task(writer(ws))


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
