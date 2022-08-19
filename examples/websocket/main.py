from websockets.test import client_test
import uasyncio
import time


while not net.isconnect():
    time.sleep_ms(200)

loop = uasyncio.get_event_loop()
loop.run_until_complete(client_test())
