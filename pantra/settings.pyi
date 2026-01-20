from __future__ import annotations

import typing
import logging
from pathlib import Path

if typing.TYPE_CHECKING:
    from types import ModuleType
    from .workers.base import BaseWorkerClient, BaseWorkerServer
    from .components.render.renderer_base import RendererBase
    from .routes import BaseRouter

logger = logging.getLogger("pantra.system")

class SafeConfig:
    WIPE_LOGGING: bool

class LazyConfig:
    BASE_PATH: Path
    WEB_PATH: str
    COMPONENTS_PATH: Path
    PAGES_PATH: Path
    CSS_PATH: Path
    JS_PATH: Path
    APPS_PATH: Path
    STATIC_DIR: str
    ALLOWED_DIRS: dict[str, Path]
    CACHE_PATH: Path

    DEFAULT_APP: str
    PRODUCTIVE: bool
    RUN_CACHED: bool

    MIN_TASK_THREADS: int
    MAX_TASK_THREADS: int
    CREAT_THREAD_LAG: int
    KILL_THREAD_LAG: int
    THREAD_TIMEOUT: int

    SOCKET_TIMEOUT: int
    WS_HEARTBEAT_INTERVAL: float | None
    SESSION_TTL: int
    MAX_MESSAGE_SIZE: int
    LOCKS_TIMEOUT: int
    SHOTS_PER_SECOND: int

    BOOTSTRAP_FILENAME: Path
    APP_TITLE: str
    DEFAULT_RENDERER: str | type[RendererBase]
    ROUTER_CLASS: str | type[BaseRouter]

    WORKERS_MODULE: str | ModuleType
    WORKER_SERVER: type[BaseWorkerServer]
    WORKER_CLIENT: type[BaseWorkerClient]

    WIPE_LOGGING: bool
    LOG_LEVEL: typing.Literal["error", "warning", "info", "debug"]
    ENABLE_WATCHDOG: bool
    SETUP_LOGGER: typing.Callable[[int], None]

    ZMQ_LISTEN: str
    ZMQ_HOST: str

    JS_SERIALIZER_LOGGING: bool
    JS_WS_LOGGING: bool
    JS_PROTO_LOGGING: bool
    JS_ADD_IDS: bool
    
    def __getattr__(self, item) -> typing.Any:
        ...


safe_config: SafeConfig = SafeConfig()
config: LazyConfig = LazyConfig()
