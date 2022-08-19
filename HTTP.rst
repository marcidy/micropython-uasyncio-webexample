Tiny Asyncio HTTP server for micropython
========================================

Who DOESN'T need to serve some files over http on their micropython device?

This does it with asyncio and with extremely limited functionality.

The goal here is not to be fully featured, but to aid in settings up basic services on a device
which can then host small things like configuring a wifi connection, basic diagnostics, etc.

Example
-------
If you want to see it in action, it's part of a worked example here:
http://github.com/marcidy/micropython-uasyncio-webexample.

http/web.py
-----------
`server(reader, writer)` is used with `uasyncio.start_server(server, host, port)` and is
called on new connections.

The server is really chatty at the moment with lots of print statements so you can see what's
going on.  I'll quiet those with a debug flag at some point.

The `route(location, resource)` function is used to match the requested route (say 'static/jquery-min.js`)
with the resource on the filesytem that will be served (say '/www/jquery-3.5.1.js').  `route` is synchronous, 
but turns the resource into an async coroutine with the `pre_route` function.  This is a bit convoluted,
but will allow expansion over time.  The result of calling `route` is that the module dict `routes` is
population with pairs like::

    routes = {
        b'/': b'/www/page.htm',
        b'/style.css': b'/www/style.css',
        b'/static/jquery-min.js': b'/www/jquery-3.5.1.js'
    }

Note that the entries are all decoded strings (b"").  This works better with the raw data coming over
the socket.  Note we don't serve right off the filesystem.  This lets you control what can be accessed.

`send_file(writer, file)` serves the item located at `file` via a chunked transfer.  This can be html, js,
anything.  It's quite simple, however.  It's sufficient to send over an html page and the jquery library
and do some fancy stuff client side instead of server side.

Enhancements welcome, but we're trying to keep it small, so it realy ought to be something you can't do
but is realy useful.

Or ever better, make it modular to add handlers on the fly and have a repo of handlers.
