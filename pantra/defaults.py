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
DEFAULT_APP = 'Core'
PRODUCTIVE = False

MIN_TASK_THREADS = 2
MAX_TASK_THREADS = 100
CREAT_THREAD_LAG = 3
KILL_THREAD_LAG = 300
THREAD_TIMEOUT = 180

SOCKET_TIMEOUT = 180
MAX_MESSAGE_SIZE = 4 * 1024 * 1024
LOCKS_TIMEOUT = 5

BOOTSTRAP_FILENAME = COMPONENTS_PATH / "bootstrap.html"

ENABLE_LOGGING = False


