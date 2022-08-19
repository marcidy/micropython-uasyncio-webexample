import uasyncio
from controllers import init
from apps.utils import load_app_cfg
from websockets.server import serve


async def on_connect(ws, path):
    print("Client connection to {}".format(path))

    async for msg in ws:
        await ws.send(msg)


def app_main(args):
    init()
    config = load_app_cfg()['echoserver']
    listen_addr = config['listen_addr']
    listen_port = config['listen_port']
    print("starting echo server on {}:{}".format(listen_addr, listen_port))
    uasyncio.create_task(serve(on_connect, listen_addr, listen_port))
    loop = uasyncio.get_event_loop()
    loop.run_forever()
