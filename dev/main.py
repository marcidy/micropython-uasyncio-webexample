from machine import reset
import sys
from apps.utils import (
    load_app_cfg,
    recovery,
)


def app_main(args):
    ''' a 'default' app_main function which is called if the import from apps
    fails '''
    recovery()

# try to load application configuration and load target app
try:
    app_cfg = load_app_cfg()
    if not app_cfg:
        raise ValueError("No app config")
    app = app_cfg.get('app')
    if not app:
        raise ValueError("No app defined in app config")
    modline = "from apps.{}.main import app_main".format(app)
    exec(modline)
except Exception as e:
    # don't fail here, app_main is still runnable and will launch recovery
    sys.print_exception(e)


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
