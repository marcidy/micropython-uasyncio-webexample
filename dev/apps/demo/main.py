import uasyncio
from controllers import init
from apps.utils import load_app_cfg
from http.web import server as http_server, route
from websockets.server import serve as websocket_server
from apps.demo.ws import add_client, call_home


def app_main(args):
    init()
    route(b'/', '/www/page.htm')
    route(b'/static/jquery.js', '/www/jquery-3.5.1.min.js')
    config = load_app_cfg()['demo']
    uasyncio.create_task(
        uasyncio.start_server(
            http_server,
            config['http']['ip'],
            config['http']['port']))
    uasyncio.create_task(
        websocket_server(
            add_client,
            config['websocket']['ip'],
            config['websocket']['port']))
    uasyncio.create_task(
        call_home(
            config['home']['ip'],
            config['home']['port']))

    loop = uasyncio.get_event_loop()
    loop.run_forever()
