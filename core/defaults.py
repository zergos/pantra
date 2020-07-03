import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_PATH = os.path.join(BASE_PATH, 'components')
PAGES_PATH = os.path.join(BASE_PATH, 'pages')
CSS_PATH = os.path.join(BASE_PATH, 'css')
APPS_PATH = os.path.join(BASE_PATH, 'apps')

TASK_THREADS = 2
SOCKET_TIMEOUT = 180
MAX_MESSAGE_SIZE = 4 * 1024 * 1024
LOCKS_TIMEOUT = 5

DEFAULT_APP = COMPONENTS_PATH #os.path.join(BASE_PATH, 'apps', 'score_parser')
