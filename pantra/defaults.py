import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_PATH = os.path.join(BASE_PATH, 'components')
PAGES_PATH = os.path.join(BASE_PATH, 'pages')
CSS_PATH = os.path.join(BASE_PATH, 'css')
JS_PATH = os.path.join(BASE_PATH, 'js')
APPS_PATH = os.path.join(BASE_PATH, 'apps')

MIN_TASK_THREADS = 2
MAX_TASK_THREADS = 100
CREAT_THREAD_LAG = 3
KILL_THREAD_LAG = 300
THREAD_TIMEOUT = 180

SOCKET_TIMEOUT = 180
MAX_MESSAGE_SIZE = 4 * 1024 * 1024
LOCKS_TIMEOUT = 5

DEFAULT_APP = COMPONENTS_PATH #os.path.join(BASE_PATH, 'apps', 'score_parser')
