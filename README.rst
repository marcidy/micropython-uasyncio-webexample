Description
===========
This repository has been reworked to be an example of how to use tools from my other repositories.

I'm not realy clear the best way to package this stuff for micropython but also have a repo full 
of documentation, examples, and tests.  This repo may be that.  I'll stick the actual tools in 
other, small repos that just have the micropython focussed packages.  Comments welcome.


Note about TLS
--------------
TLS support is currently blocked in micropython due to memory constraints.  I have begun work
on these tools to support it at least client side and made some attempts for server side support
but until the memory issues are resolved in micropython, the support won't be complete.

/dev
----
The /dev directory holds a working example.  Nothing *has* to be done this way, I just chose
these methods as examples.

JSON config files
-----------------

Just an example of how to manange configuraiton with json files.  I have used btree
key/value dbs for the same purpose with success, and NVS partitions are also 
candidates.  I'll add examples for those down the road.

networking credentials and locations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
These settings are used to identify the device, start an access point, and connect to a 
local access point as a wifi station.  Angle brackets mean fill this information in.
Feel free to change anything.  This file is checked on boot in all cases.

Look in `controllers.py` to see how these settings are consumed.

network.json::

    {
        "device": {
            "iam": "Device_1",
            "dev": "ESP32"
        },
        "ap": {
            "essid": "<device AP ssid>",
            "authmode": 3,
            "password": "<device AP password>",
            "hidden": false
        },
        "sta": {
            "ssid": "<AP ssid>",
            "pass": "<AP password>"
        },
        "wsserver": {
            "ip": "192.168.3.1",
            "host": 'server.tld'
            "port": 7777,
            "path": "TS001"
        }
    }



application configuration
^^^^^^^^^^^^^^^^^^^^^^^^^
The default application to load and application settings.  The only settings
that need customization are the "home" ip and port in the demo to point to the
machine running the device_server.

app.json::
    
    {
        "app": "demo",
        "echoserver": {
            "listen_addr": "0.0.0.0",
            "listen_port": 7777
        },
        "demo": {
            "http": {
                "ip": "0.0.0.0",
                "port": 80
            },
            "websocket": {
                "ip": "0.0.0.0",
                "port": 7777
            },
            "home": {
                "ip": "192.168.3.1",
                "port": 7770
            }
        }
    }


The value associated with "app" will be loaded by the application loading in `main.py`.  
This value must exists as a key in the file, whose values represt configuration for
that app.

/certs
------
Ignore this directory for now, will hold keys and things for tls implementation

/www
----
web root for html requests to the http server.  The demo page is in there and uses
jquery as an example of how to self-contain some helpful js for a nice intro page.

/controllers.py
---------------
There are some "important" object instances and initialization routines in here 
which are used elsewhere, like the network station and access point interfaces, and a
"fake_interface" which is used in the demo page.

The fake_interface takes a string and upper cases it. 

This is done via websocket connection between the loaded page and the device, and
represents a way to interact between the device and the page.  This could be an
interface to additional hardare, for example.

The networking interface initialization "works" with micropython v1.19.1.  Using
soft-resets (ctrl-D) can cause some errors to be thrown but the initial connection
should be robust.  Monitoring the connection is not implemented.

The `init()` function is called on boot to connect the interfaces.

The `recovery()` function is called when booting fails or the application exits
with an unhandled exception.

/main.py
--------
main.py does a lot of things differently from how standard python is taught.  This
is because it's more systems programming than application programming.

A default `app_main(args)` is defined whose purpose is to run if the import
of the desired application's `app_main` fails.  All applications (in this
scheme anyways) have the following structure::

    apps.<application>.main.app_main

where <application> is the application name in app.json.

main.py trys to load app.json and read the application name::

    try:                                                                            
        app_cfg = load_app_cfg()                                                    
        if not app_cfg:                                                             
            raise ValueError("No app config")                                       
        app = app_cfg.get('app')                                                    
        if not app:                                                                 
            raise ValueError("No app defined in app config") 


Since we're trying to load an application by variable, the import line is 
constructured and run through "exec()"::

        modline = "from apps.{}.main import app_main".format(app)                   
        exec(modline)  

Exceptions aren't handled, just printed.  This is becuase there's a severe
unexpected error: the app we want to load isn't loading.

This is why `app_main` was defined.  If the app loaded, `app_main` would point 
to the application we want to run.  Since it wasn't loaded, it defaults to run
the `recovery()` function as defined::

    def app_main(args):
        ''' a 'default' app_main function which is called if the import from apps
        fails '''
        recovery()

Now app_main is run::

    try:                                                                            
        app_main(None)                                                              
    except KeyboardInterrupt:                                                       
        sys.exit()                                                                  
    except Exception as e:                                                          
        sys.print_exception(e)                                                      
        recovery()                                                                  
    except BaseException as e:                                                      
        sys.print_exception(e)                                                      
        recovery()

In this case, a KayboardInterrupt will drop to the shell, while the other two main
classes of exceptions will cause `recovery()` to run.

The application loader does not know or care about the application.  The application
ought to handle it's own exceptions.  If an excepetion is raised to here, the best
we can do is try to put the device into a recoverable state.

/apps
-----

The applications we intent to run, synced with app.json.


/apps/utils.py
^^^^^^^^^^^^^^
Some helpers, like what to do for recovery and loading config files only once.

/apps/echoserver
^^^^^^^^^^^^^^^^
Reads the configuration and launches a websocket server which repeats back to what you send.

Useful for testing as it's simple.  Use `scripts/echo_client.py` to interact with it from a 
different machine on the same network.  Make sure the server ip and port match in both.

/apps/demo
^^^^^^^^^^
The main dealy.  The device will run a http serer and a websocket server, and will launch a
websocket client attempting to contact the device_server.  Run the device_server in the 
/scripts directory.

If you connect to the device access point, or are on the same network as the device, navigate
your web browser to it's ip address::

    http://192.168.4.1
    or
    http://192.168.1.100 # or whatever it's ip address is on your network

If everything is working, you should be greeted with a page which shows you information
about the device and has a card for Fake Interface Example.

Start the fake interface via the button.
Verify it's running.
Send it a message.
Read the glorified, all capitalized message, fully processed on the device.

Troubleshooting
---------------
Oof, sorry you are here.

There's a lot of output on the device side, there might be helpful information there.

edit "app.json" so that "app" is now "echoserver" and upload that change to the device and 
reboot.  Run the echo_client.py in scripts and verify the device and computer are talking
to each other.

In when running the "demo" app, you can connect to the device as an AP, try that, might be
easier than dealing with all the intermediate networking issues which can arise.

