import logging
from pathlib import Path
import importlib.util

def get_proj_path():
    cwd = Path('.').absolute()
    while cwd.name:
        if (cwd / 'components' / 'bootstrap.html').exists():
            return cwd
        cwd = cwd.parent
    return Path('.')

BASE_PATH = get_proj_path()
WEB_PATH = ''
COMPONENTS_PATH = BASE_PATH / 'components'
PAGES_PATH = BASE_PATH / 'pages'
CSS_PATH = BASE_PATH
JS_PATH = Path(importlib.util.find_spec('pantra').origin).parent / 'js'
APPS_PATH = BASE_PATH / 'apps'
STATIC_DIR = 'static'
ALLOWED_DIRS = {}

DEFAULT_APP = 'Core'
PRODUCTIVE = False

MIN_TASK_THREADS = 2
MAX_TASK_THREADS = 100
CREATE_THREAD_LAG = 3
KILL_THREAD_LAG = 300
THREAD_TIMEOUT = 180

SOCKET_TIMEOUT = 180
WS_HEARTBEAT_INTERVAL = None
SESSION_TTL = 1800
MAX_MESSAGE_SIZE = 4 * 1024 * 1024
LOCKS_TIMEOUT = 5

BOOTSTRAP_FILENAME = COMPONENTS_PATH / "bootstrap.html"
APP_TITLE = "Pantra Web App"
DEFAULT_RENDERER = 'pantra.components.render.renderer_html.RendererHTML'

ENABLE_LOGGING = False
ENABLE_WATCHDOG = False

def setup_logger(level: int = logging.DEBUG):
    logger = logging.getLogger("pantra.system")
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.debug("Logger configured")

SETUP_LOGGER = setup_logger

WORKERS_MODULE = 'pantra.workers.memory'

ZMQ_LISTEN = 'tcp://*:5555'
ZMQ_HOST = 'tcp://localhost:5555'

JS_SERIALIZER_LOGGING = False
JS_WS_LOGGING = False
JS_PROTO_LOGGING = False
JS_ADD_IDS = False
