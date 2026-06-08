from __future__ import annotations

import sys
import typing
import logging
import logging.config
from pathlib import Path
import importlib.util

__all__ = ['Config']

if typing.TYPE_CHECKING:
    from .components.render.renderer_base import RendererBase
    from .routes import BaseRouter
    from .workers.base import BaseWorkerServer, BaseWorkerClient
    from .session_storage import SessionStorage

def get_proj_path():
    if 'sphinx._cli' in sys.modules:
        print("*** sphinx is detected - fake mode enabled ***")
        Path.__repr__ = lambda self: f'Path({self.as_posix()!r})'
        return Path('.')

    cwd = Path('.').absolute()
    while cwd.name:
        if (cwd / 'components' / 'bootstrap.html').exists():
            return cwd
        cwd = cwd.parent
    return Path('.')

def get_module_path():
    if 'sphinx._cli' in sys.modules:
        return Path('pantra')
    return Path(importlib.util.find_spec('pantra').origin).parent

def setup_logger(self, level: int = logging.DEBUG):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                '()': "logging.Formatter",
                "fmt": "%(asctime)s - %(levelname)s - %(threadName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "stderr": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "stdout": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "pantra": {"handlers": ["stdout"], "level": level},
            "uvicorn": {"handlers": ["stderr"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": ["stderr"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["stdout"], "level": level, "propagate": False},
        },
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger("pantra.system")
    logger.debug("Logger configured")


class Config:
    """Default configuration class"""

    BASE_PATH: Path = get_proj_path()  #: Base project path
    WEB_PATH: str = ''  #: Own web application URL to refer web resources
    COMPONENTS_PATH: Path = BASE_PATH / 'components'  #: Path to `components` directory
    CSS_PATH: Path = BASE_PATH / 'css'  #: Path to common CSS files
    JS_PATH: Path = get_module_path() / 'js'  #: Path to `pantra` engine JS core
    APPS_PATH: Path = BASE_PATH / 'apps'  #:  Path to `apps` directory
    CACHE_PATH: Path = BASE_PATH / 'cached'  #: Path to pre-cached components
    STATIC_DIR: str = 'static'  #: Default subdirectory name to contain static media (font, images, etc.)
    ALLOWED_DIRS: dict[str, Path] = {}  #: Dictionary `alias -> full path` to allow static links

    DEFAULT_APP: str = 'Core'  #: Default app name
    DEFAULT_LANGUAGE: str = 'en' #: Default language `code <https://www.unicode.org/cldr/charts/48/supplemental/territory_language_information.html>`__
    PRODUCTIVE: bool = False  #: Flag app as "productive-ready"
    RUN_CACHED: bool = False  #: Load components from :doc:`pre-cached <cache>` directory

    MIN_TASK_THREADS: int = 2  #: Min. amount of threads to execute clicks/callbacks
    MAX_TASK_THREADS: int = 100  #: Max. amount of threads. Check :doc:`threads <threads>`
    CREATE_THREAD_LAG: int = 3  #: Time in seconds to wait for relaxed thread before create one
    KILL_THREAD_LAG: int = 300  #: Kill redundant threads after specified amount of seconds
    THREAD_TIMEOUT: int = 0  #: Kill occupied thread if it hangs for too long

    SOCKET_TIMEOUT: int = 180  #: Amount of seconds to wait websocket connection restored
    WS_HEARTBEAT_INTERVAL: float | None = None  #: Websocket ping interval to support connection
    SESSION_TTL: int = 1800  #: Reset passive user session after specified amount of seconds
    MAX_MESSAGE_SIZE: int = 4 * 1024 * 1024  #: Websocket max message size in bytes
    LOCKS_TIMEOUT: int = 5  #: Amount of seconds to wait requested data from client side
    SHOTS_PER_SECOND: int = 25  #: Max fps for flickering shots (resize, grab/move, etc)

    BOOTSTRAP_FILENAME: Path = COMPONENTS_PATH / "bootstrap.html"  #: Path to bootstrap :doc:`template <template>`
    APP_TITLE: str = "Pantra Web App"  #: Page title in the browser
    DEFAULT_RENDERER: str | type[RendererBase] = '{pantra.components.render.renderer_html:RendererHTML}'  #: Canonic path to default :doc:`renderer <renderer>` class
    #DEFAULT_RENDERER = 'pantra.cached.renderer:RendererCached'
    ROUTER_CLASS: str | type[BaseRouter] = '{pantra.routes:DevRouter}'  #: Canonic path to HTTP router
    #ROUTER_CLASS = 'pantra.routes:CachedRouter'

    WIPE_LOGGING: bool = False  #: Eliminate `pantra` core logs on byte-code level
    LOG_LEVEL: typing.Literal["error", "warning", "info", "debug"] = "info"  #: Set logger depth
    ENABLE_WATCHDOG: bool = False  #: Watch for files updates in real-time to reload components

    SETUP_LOGGER: typing.Callable[[int], None] = setup_logger  #: Reference to setup logger function (arg is `logging.LEVEL`)

    WORKERS_MODULE: str = '{pantra.workers.memory}'  #: Canonical path to :doc:`message queue <message_queue>` module
    WORKER_SERVER: type[BaseWorkerServer] = None
    WORKER_CLIENT: type[BaseWorkerClient] = None

    SESSION_STORAGE: str | type[SessionStorage] = '{pantra.session_storage:NullSessionStorage}'  #: User settings storage, see :class:`~pantra.session_storage.SessionStorage`

    ZMQ_LISTEN: str = 'tcp://*:5555'  #:  URI for ZeroMQ listener
    ZMQ_HOST: str = 'tcp://localhost:5555'  #: URI for ZeroMQ connection

    JS_SERIALIZER_LOGGING: bool = False  #: Dump to dev console serializer details
    JS_WS_LOGGING: bool = False  #: Dump to dev console websocket connection details
    JS_PROTO_LOGGING: bool = False  #: Dump to dev console websocket messages
    JS_ADD_IDS: bool = False  #: Render explicit `id` attributes to each HTML node
