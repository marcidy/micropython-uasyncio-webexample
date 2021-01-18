## Description
It's a really basic http server, websocket server and websocket client with a "fake interface" which could run anything.

It's really just an example of a webpage loaded from an ESP32 which connects back to the ESP32 via a websocket to exchagne information. 


## Wow, the code is really undocumented and messy
Yeah, I ripped the example out of a private project.  Sorry.  Maybe I'll update the docs over time, but tbh the project is intended as an example for people to roll their own stuff in composable units rather than a monolithic solution.  For example. I only serve static files, and I can serve JQuery by implementing chunked transfers for all the files.  Someone else might not want/need that at all.

## What to change to get it to work
1) Chagne the wifi access point details in main.py
2) If you want to use device as an access point, import the ap from controllers.py.  The interfaces are instanciated in one place so I can access them in various places.
3) ws.py has a `phone_home` coroutine which statically defines a server to try an contact. It looks goofy becuase I don't actually do it this way.  you could change this to pass an arg when instanciating the coroutine in main.py.

theoretically this will "just work" and you can navigate to `http://<device ip>/` and get a simple interface. At the bottom you can start the `fake_interface` task, send a message into it and receive a response (just echos the message.to_upper().

The wifi connection stuff might actually work, or i may have broken it a bit.  I'll give a better look later.  It's a bit tricky to figure out if you pass a bad password into the networking interface, as it's not directly observable.  Sorry, but at least it can get you started to boot the device to an AP mode, connect to it from your phone, and configure the wifi credentails.  Maybe.  Hopefully.

## Websocket notes
The core of the websockets was done by modifying https://github.com/danni/uwebsockets to use the asyncio avaialble in micropython v1.13+.  All the hard work done by them.  It was so well constructed I just peppered in a few asyncs and awaits and added the server handshake.

The interface follows python websockets: https://websockets.readthedocs.io/en/stable/

It's not exact but close enough that they interoperate fine from what I can tell.  Both client and server interoprate.

### Phone Home
If you run a websocket server elsewhere, change `phone_home` in `ws.py`, which attemps to phone home evecy 5 seconds.  If a connection is made, data will be sync'd to that location also.

## HTTP server notes
I use a dict and a deferred async call for simple routing rather than serve data from the filesystem.  

This way I don't care what request is received.  right now only static pages are served, but this could be exteded to a templated page if you want.  I personally don't want the device doing complicated things.  Creating a "templated" function similar to the "route" function would work fine.

page.htm shows what's expected acorss the ws interface.
I'm using JQuery, and that required chunked file transfers

Feel free to raise isses and stuff if the example doesn't work.  Feature requests probably need a pull requests, but again, this is really meant as an example :)
