import gc
import uasyncio
import json
import time
from controllers import net, ap, fake_interface
from websockets import client


cid = 0
clients = set()
tasks = {}

iam = "Device_1"
dev = "ESP32"

state = {
    "iam": iam,
    "dev": dev,
    "fake_interface/running": False,
}


async def send(data):
    # print(data)
    await uasyncio.gather(*[cl.send(data) for cl in clients])


async def wifi(ws):
    await ws.send('{"info": "Querying networking..."}')
    if ap:
        await ws.send('{{"wifi/ap/active": "{}"}}'.format(ap.active()))
        await ws.send('{{"wifi/ap/ssid": "{}"}}'.format(ap.config('essid')))
    else:
        await ws.send('{{"wifi/ap/active": "{}"}}'.format(False))
    if net:
        await ws.send('{{"wifi/net/active": "{}"}}'.format(net.active()))
        mac = (("{:02X}:"*6)[:-1]).format(*net.config('mac'))
        await ws.send('{{"wifi/net/mac": "{}"}}'.format(mac))
        await ws.send('{{"wifi/net/ap": "{}"}}'.format(net.config('essid')))
        connected = net.isconnected()
        await ws.send('{{"wifi/net/connected": "{}"}}'.format(connected))
        if connected:
            ip, mask, gw, dns = net.ifconfig()
            await ws.send('{{"wifi/net/ip": "{}"}}'.format(ip))
            await ws.send('{{"wifi/net/gw": "{}"}}'.format(gw))
            await ws.send('{{"wifi/net/dns": "{}"}}'.format(dns))

    else:
        await ws.send('{{"wifi/net/active": "{}"}}'.format(False))
    await ws.send('{"info": "Done"}')


async def scan_new_network(sta_ssid):
    if not net.active():
        net.active(1)

    for an_ap in net.scan():
        if an_ap[0] == sta_ssid.encode('ascii'):
            return True
    return False


async def watch_connection():
    start_time = time.time()
    while time.time() - start_time < 10:
        if net.isconnected():
            return True
        await uasyncio.sleep_ms(500)
    return False


async def test_new_sta(args=None):
    if not args or len(args) < 1 or len(args) > 2:
        await send('{"error": "Bad args for wifi, need at least 1, no more than 2"}')
        return

    ssid = args[0]
    wifi_pass = None
    if len(args) == 2:
        wifi_pass = args[1]
    if wifi_pass == "":
        wifi_pass = None

    await send('{"info": "Starting network scan"}')
    scan_result = await scan_new_network(ssid)

    if scan_result:
        await send('{"info": "Network Found"}')
        await send('{"info": "Attempting Connection"}')
        net.disconnect()
        try:
            if wifi_pass:
                net.connect(ssid, wifi_pass)
            else:
                net.connect(ssid)
        except Exception:
            net.connect()
            return
    else:
        await send('{"wifi/test/result": "Fail"}')
        await send('{{"info": "Network {} Not Found"}}'.format(ssid))
        return

    con_ssid = net.config("essid")
    success = "Success" if con_ssid == ssid else "Fail"
    if net.isconnected():
        await send('{{"wifi/test/result": "{}"}}'.format(success))
        ip, mask, gw, dns = net.ifconfig()
        await send('{{"wifi/sta/new_test": "{}"}}'.format(True))
        await send('{{"wifi/sta/connected": "{}"}}'.format(True))
        await send('{{"wifi/sta/ip": "{}"}}'.format(ip))
        await send('{{"wifi/sta/gw": "{}"}}'.format(gw))
        await send('{{"wifi/sta/dns": "{}"}}'.format(dns))
    else:
        net.connect()


async def send_message(args=None):
    if not args or len(args) > 1:
        await send('{"error": "Bad args for Send Message"}')
        return

    if 'fake_interface' not in tasks:
        await send('{"error": "Fake Interface not running"}')

    fake_interface.send(args[0])


async def run_fake_interface():
    while True:
        fake_interface.run()
        while fake_interface.to_rec:
            msg = fake_interface.recv()
            await send('{{"fake_interface/msg": "{}"}}'.format(msg))
        await uasyncio.sleep_ms(250)


async def start_fake_interface(args=None):
    if 'fake_interface' in tasks:
        return

    tasks['fake_interface'] = uasyncio.create_task(run_fake_interface())
    state['fake_interface/running'] = True


async def stop_fake_interface(args=None):
    if 'fake_interface' not in tasks:
        return
    else:
        task = tasks.pop('fake_interface')
        task.cancel()
        state['fake_interface/running'] = False


get_router = {
    'wifi': wifi,
}

cmd_router = {
    'test_new_sta': test_new_sta,
    'send_message': send_message,
    'start_interface': start_fake_interface,
    'stop_interface': stop_fake_interface,
}


async def process(ws, data):
    print("Handling: {}".format(data))
    gc.collect()
    try:
        cmd, item, args = json.loads(data)
    except Exception as e:
        gc.collect()
        await ws.send('{"error": "Malformed Request"}')
        await ws.send(json.dumps({'error': data}))
        await ws.send('{{"error": "{}"}}'.format(e))
        gc.collect()
        return

    if cmd == "GET":
        if item in get_router:
            await get_router[item](ws)
    if cmd == "CMD":
        if item in cmd_router:
            if args:
                await cmd_router[item](args)
            else:
                await cmd_router[item]()
    gc.collect()


async def register(ws):
    print("register")
    clients.add(ws)


async def unregister(ws):
    print("unregister")
    clients.remove(ws)


async def add_client(ws, path):
    print("Client Connection to {}".format(path))
    await register(ws)

    try:
        await send(json.dumps(state))
        async for msg in ws:
            await process(ws, msg)
            await send(json.dumps(state))
    finally:
        await unregister(ws)
        if not net.isconnected():
            net.connect()


async def call_home():
    connected = False
    server = "mywebsocsket.server.com"
    uri = "ws://" + server + ":7777/" + iam
    while True:
        if not connected:
            try:
                ws = await client.connect(uri)
                if ws:
                    connected = True
                    uasyncio.create_task(add_client(ws, "/" + iam))
            except Exception:
                connected = False
        else:
            connected = ws.open
        await uasyncio.sleep(5)
