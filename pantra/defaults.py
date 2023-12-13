import logging
from pathlib import Path
import pkg_resources

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
CSS_PATH = BASE_PATH / 'css'
JS_PATH = Path(pkg_resources.resource_filename('pantra', "js"))
APPS_PATH = BASE_PATH / 'apps'
STATIC_DIR = 'static'

DEFAULT_APP = 'Core'
PRODUCTIVE = False

MIN_TASK_THREADS = 2
MAX_TASK_THREADS = 100
CREATE_THREAD_LAG = 3
KILL_THREAD_LAG = 300
THREAD_TIMEOUT = 180

SOCKET_TIMEOUT = 180
MAX_MESSAGE_SIZE = 4 * 1024 * 1024
LOCKS_TIMEOUT = 5

BOOTSTRAP_FILENAME = COMPONENTS_PATH / "bootstrap.html"
APP_TITLE = "Pantra Web App"

ENABLE_LOGGING = False

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

ZMQ_HOST = 'localhost'
ZMQ_PORT = 5555
