import network

net = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)


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
