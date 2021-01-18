import uasyncio
import webrepl
from controllers import net
from http.web import server
from ws import add_client, call_home
from websockets.server import serve


net.active(1)
net.connect("My AP", "Password")
webrepl.start(password="test")


async def main():
    await uasyncio.start_server(server, '0.0.0.0', 80)
    await serve(add_client, '0.0.0.0', 7777)

uasyncio.create_task(call_home())
loop = uasyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
