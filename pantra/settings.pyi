from pathlib import Path

class Config:
    BASE_PATH: Path
    WEB_PATH: str
    COMPONENTS_PATH: Path
    PAGES_PATH: Path
    CSS_PATH: Path
    JS_PATH: Path
    APPS_PATH: Path
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

    ENABLE_LOGGING: bool


config: Config = Config()
