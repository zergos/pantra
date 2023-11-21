from pathlib import Path

class Config:
    BASE_PATH = Path(__file__).parent.parent
    COMPONENTS_PATH = BASE_PATH / 'components'
    PAGES_PATH = BASE_PATH / 'pages'
    CSS_PATH = BASE_PATH / 'css'
    JS_PATH = BASE_PATH / 'js'
    APPS_PATH = BASE_PATH / 'apps'
    DEFAULT_APP = 'Core'

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


config: Config = Config()