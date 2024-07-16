from __future__ import annotations

import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from .workers.base import BaseWorkerClient, BaseWorkerServer

class Config:
    BASE_PATH: Path
    WEB_PATH: str
    COMPONENTS_PATH: Path
    PAGES_PATH: Path
    CSS_PATH: Path
    JS_PATH: Path
    APPS_PATH: Path
    STATIC_DIR: str
    ALLOWED_DIRS: dict[str, Path]

    DEFAULT_APP: str
    PRODUCTIVE: bool

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

    BOOTSTRAP_FILENAME: Path
    APP_TITLE: str

    WORKERS_MODULE: str
    WORKER_SERVER: type[BaseWorkerServer]
    WORKER_CLIENT: type[BaseWorkerClient]

    ENABLE_LOGGING: bool
    SETUP_LOGGER: typing.Callable[[], None]

    ZMQ_LISTEN: str
    ZMQ_HOST: str

    JS_SERIALIZER_LOGGING: bool
    JS_WS_LOGGING: bool
    JS_PROTO_LOGGING: bool
    JS_ADD_IDS: bool

    def __getattr__(self, item):
        ...


config: Config = Config()
