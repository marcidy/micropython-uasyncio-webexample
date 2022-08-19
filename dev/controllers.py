import network
import json
import time


net = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
config = {}


def load_config():
    with open("/network.json", 'r') as f:
        data = json.load(f)

    if data:
        config.update(**data)

load_config() # need it done on import


class FakeInterface:

    def __init__(self):
        self.sent = 0
        self.received = 0
        self.to_send = []
        self.to_rec = []

    def send(self, msg):
        self.to_send.append(msg)

    def recv(self):
        if self.to_rec:
            return self.to_rec.pop()

    def run(self):
        while self.to_send:
            msg = self.to_send.pop(0)
            print(msg)
            self.to_rec.append(msg.upper())


fake_interface = FakeInterface()


def init_sta():
    ssid = config['sta'].get('ssid')
    pwrd = config['sta'].get('pass')

    if not ssid:
        raise ValueError("No SSID in network.json")

    net.active(1)
    if not net.status() in [
            network.STAT_IDLE,
            network.STAT_GOT_IP,]:
        net.disconnect()

    try:
        net.connect(ssid, pwrd)
    except OSError:
        net.disconnect()
        net.connect()

    start_time = time.time()
    while (not net.isconnected()):
        if (time.time() - start_time > 30):
            print("Connect failed")
            return False
        time.sleep(.010)

    return True


def init_ap():

    ap_config = config.get('ap')
    if not ap_config:
        return True

    ap.active(1)
    ap.config(**ap_config)
    return True


def init_webrepl():
    import webrepl
    webrepl.start(password="test")


def init():
    load_config()
    init_sta()
    init_ap()
    init_webrepl()
