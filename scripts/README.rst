Scripts
=======
Helpers scripts I run on my debian machine.

requirements.py
---------------

Python requirements to run the scripts

echo_client.py
--------------
A simple websockets based client.  Use this with the "echoserver" example.

It asks for the uri to connect to the echo server as "ws://<server ip>:<port>" and will attempt
to connect.

Is set to log in debug mode so you'll see pings and pongs.

e.g. if the device has ip 192.168.1.114 and the echoserver port is set to 7890:
usage::
    
    $ python echo_client.py
    websocket server uri [ws://192.168.4.1:7777]: ws://192.168.1.114:7890
    = connection is CONNECTING
    > GET / HTTP/1.1
    > Host: 192.168.1.114:7890
    > Upgrade: websocket
    > Connection: Upgrade
    > Sec-WebSocket-Key: FgkVdWpmh9iuwtjQxyF/eA==
    > Sec-WebSocket-Version: 13
    > Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
    > User-Agent: Python/3.10 websockets/10.1
    < HTTP/1.1 101 Switching Protocols
    < Upgrade: websocket
    < Connection: Upgrade
    < Sec-WebSocket-Accept: q8bxu70GcvzYecW7xN1CVC9zyNc=
    < Server: Micropython
    = connection is OPEN
    >>> % sending keepalive ping
    > PING a2 8b 96 01 [binary, 4 bytes]
    < PONG a2 8b 96 01 [binary, 4 bytes]
    % received keepalive pong
    % sending keepalive ping
    > PING 3c cd 30 c7 [binary, 4 bytes]
    < PONG 3c cd 30 c7 [binary, 4 bytes]
    % received keepalive pong


The ping and pong will continue, this shows that the websocket server is running well,
responding to ping requests.


device_server.py
----------------
Basically a pipe for devices to chat with webpages.

run the server like::
    
    $ python device_server.py

it will block, which is fine, you can make it into a service if you want.  It creates
a log file.

It's confgured to run a "device" server on port 7770 and a "page" server on 7771.  Note
that it's listening on all interfaces, so "as-is" don't run this anywhere public.

Assuming the laptop, desktop, raspberry pi, or whatever it runs on is on the same
network as the micropython device, point the device to this server by editing "app.json".

When things are working well, the device will connect with the name configured in
"network.json"::

    Device connected: /Device_1

When the device is connected to the device server, you can point a web page to the
page server, and they will interact.  Multiple pages can be connected to a single
device.


device_server.log
-----------------
Not included, but is created by the device_server. You can watch the messages being 
exchanged by inspecting this log file.


server-gen.sh
-------------
creating keys for the eventual use of tls, which is currently blocked by memory
consumption issues.
