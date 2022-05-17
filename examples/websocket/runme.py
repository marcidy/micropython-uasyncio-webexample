from websockets.test import add_client
from websockets.ssl_server import serve
import uasyncio
import network
import webrepl


net = network.WLAN(network.STA_IF)
net.active(1)
net.connect("titopuente", "testmatt")
webrepl.start(password="test")

def main():
    wss_server = serve(add_client, "0.0.0.0", 7777)
    loop = uasyncio.get_event_loop()
    loop.run_until_complete(wss_server)
    loop.run_forever()
