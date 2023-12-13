from __future__ import annotations

import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from .workers import BaseWorkerClient, BaseWorkerServer

class Config:
    BASE_PATH: Path
    WEB_PATH: str
    COMPONENTS_PATH: Path
    PAGES_PATH: Path
    CSS_PATH: Path
    JS_PATH: Path
    APPS_PATH: Path
    STATIC_DIR: str

    DEFAULT_APP: str
    PRODUCTIVE: bool

    MIN_TASK_THREADS: int
    MAX_TASK_THREADS: int
    CREAT_THREAD_LAG: int
    KILL_THREAD_LAG: int
    THREAD_TIMEOUT: int

    SOCKET_TIMEOUT: int
    MAX_MESSAGE_SIZE: int
    LOCKS_TIMEOUT: int

    BOOTSTRAP_FILENAME: Path
    APP_TITLE: str

    WORKERS_MODULE: str
    WORKER_SERVER: type[BaseWorkerServer]
    WORKER_CLIENT: type[BaseWorkerClient]

    ENABLE_LOGGING: bool
    SETUP_LOGGER: typing.Callable[[], None]

    ZMQ_HOST: str
    ZMQ_PORT: int


config: Config = Config()
