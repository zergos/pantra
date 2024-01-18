from __future__ import annotations

import asyncio
import contextlib
import typing
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
import threading
import queue
from datetime import datetime
from enum import IntEnum, auto

from ..common import raise_exception_in_thread
from ..settings import config
from ..patching import wipe_logger

if typing.TYPE_CHECKING:
    from aiohttp import web
    from ..session import Session

logger = logging.getLogger('pantra.system')

class ThreadMode(IntEnum):
    NORMAL = auto()
    REDUCED = auto()

@dataclass
class WorkerStat:
    active: bool = False
    last_tick: float = 0
    mode: ThreadMode = ThreadMode.NORMAL
    thread: threading.Thread = None

@wipe_logger
class BaseWorkerServer(ABC):
    run_with_web: typing.ClassVar[bool] = False

    class Listener(ABC):
        @abstractmethod
        async def send(self, session_id: str, data: bytes): ...

        @abstractmethod
        async def receive(self) -> tuple[str, bytes]: ...

        @abstractmethod
        async def close(self): ...

    workers: typing.ClassVar[dict[str, WorkerStat]] = {}
    task_queue: typing.ClassVar[queue.Queue | None] = queue.Queue()
    thread_counter: typing.ClassVar[int] = 0

    listener: Listener
    async_loop: asyncio.AbstractEventLoop

    @classmethod
    def task_processor(cls):
        from ..session import Session, SessionTask
        try:
            ident = threading.current_thread().name
            while True:
                try:
                    func, args, kwargs = cls.task_queue.get(timeout=5)
                except queue.Empty:
                    if cls.workers[ident].mode == ThreadMode.REDUCED:
                        break
                    continue
                if func is None: break
                cls.workers[ident].last_tick = time.perf_counter()
                cls.workers[ident].active = True
                func(*args, **kwargs)
                cls.workers[ident].last_tick = time.perf_counter()
                cls.workers[ident].active = False
        except SystemExit:
            logger.error(f'`{ident}` thread got exit signal')

    @staticmethod
    @contextlib.contextmanager
    def wrap_session_task(session: Session, func: typing.Callable):
        from ..session import SessionTask
        session.tasks[func.__name__] = SessionTask(threading.current_thread(), func)
        yield
        if func.__name__ in session.tasks: # other thread could stop this already, or we have similar callers names
            del session.tasks[func.__name__]

    @staticmethod
    def run_coroutine(session: Session, func: typing.Callable, coro: typing.Coroutine):
        from ..session import SessionTask
        task = asyncio.run_coroutine_threadsafe(coro, session.server_worker.async_loop)
        def on_done(future):
            del session.tasks[func.__name__]

        session.tasks[func.__name__] = SessionTask(task, func)
        task.add_done_callback(on_done)

    @classmethod
    def tasks_controller(cls):
        while True:
            time.sleep(1)
            tick = time.perf_counter()
            last_tick = 0
            for k, v in list(cls.workers.items()):  # type: str, WorkerStat
                if not v.thread.is_alive():
                    logger.warning(f"Thread killed `{k}`")
                    del cls.workers[k]
                elif v.active and tick - v.last_tick > config.THREAD_TIMEOUT:
                    logger.warning(f"Thread timeout `{k}`")
                    raise_exception_in_thread(v.thread.native_id)
                    del cls.workers[k]
                elif len(cls.workers) > config.MIN_TASK_THREADS \
                        and not v.active and v.last_tick and tick - v.last_tick > config.KILL_THREAD_LAG:
                    logger.warning(f"Thread killing `{k}`")
                    v.mode = ThreadMode.REDUCED
                elif v.active and v.last_tick > last_tick:
                    last_tick = v.last_tick
            if len(cls.workers) < config.MIN_TASK_THREADS \
                    or not cls.task_queue.empty() and last_tick and tick - last_tick > config.CREAT_THREAD_LAG:
                cls.thread_counter += 1
                thread_name = f'X#{cls.thread_counter}'
                thread = threading.Thread(target=cls.task_processor, name=thread_name, daemon=True)
                logger.warning(f'New thread created `{thread_name}`')
                cls.workers[thread_name] = WorkerStat(thread=thread)
                thread.start()

    @staticmethod
    def session_killer():
        from ..session import Session
        while True:
            time.sleep(5)
            now = datetime.now()
            for session_id in frozenset(Session.sessions):
                session = Session.sessions[session_id]
                if not getattr(session, "just_connected", True) and (now - session.last_touch).seconds >= config.SESSION_TTL:
                    logger.info(f'Session {session_id} killed by TTL limit {config.SESSION_TTL} seconds')
                    for task in list(session.tasks.keys()):
                        session.kill_task(task)
                    del Session.sessions[session_id]

    @classmethod
    def start_task_workers(cls):
        logger.debug("Starting task workers")
        BaseWorkerServer.task_queue = queue.Queue()
        for i in range(config.MIN_TASK_THREADS):
            thread = threading.Thread(target=cls.task_processor, name=f'#{i}', daemon=True)
            BaseWorkerServer.workers[thread.name] = WorkerStat(thread=thread)
            thread.start()
        threading.Thread(target=cls.tasks_controller, daemon=True).start()
        threading.Thread(target=cls.session_killer, daemon=True).start()

    @abstractmethod
    def start_listener(self): ...

    async def run_processor(self):
        from ..session import Session
        from ..serializer import serializer
        from ..protocol import process_message

        logger.debug("Starting task processor")

        self.async_loop = asyncio.get_running_loop()

        while True:
            session_id, message = await self.listener.receive()
            data = serializer.decode(message)

            if data['C'] == "SESSION":
                Session(session_id, data['app'], data['lang'], data['params'])
            else:
                if (session:=Session.sessions.get(session_id, None)) is None:
                    from ..protocol import Messages
                    code = serializer.encode(Messages.reconnect())
                    await Session.server_worker.listener.send(session_id, code)
                else:
                    session.last_touch = datetime.now()
                    await process_message(session, data)


@wipe_logger
class BaseWorkerClient(ABC):
    class Connection(ABC):
        @abstractmethod
        async def send(self, message: bytes): ...

        @abstractmethod
        async def receive(self) -> bytes: ...

        @abstractmethod
        def close(self): ...

    connection: Connection
    sync_task: asyncio.Task
    last_touch: datetime

    @abstractmethod
    def open_connection(self, session_id: str): ...

    async def stop_websocket_binding(self):
        self.sync_task.cancel()
        try:
            await self.sync_task
        except asyncio.CancelledError:
            pass

    async def close_connection(self):
        await self.stop_websocket_binding()
        self.connection.close()

    def bind_to_websocket(self, ws: web.WebSocketResponse):
        async def task():
            while True:
                message = await self.connection.receive()
                self.last_touch = datetime.now()
                await ws.send_bytes(message) #, compress=len(message)>=1000)
        self.sync_task = asyncio.create_task(task())

    async def connect_session(self, session_id: str, app: str, lang: list[str], params: dict[str, str]):
        from ..serializer import serializer

        logger.debug("Initiate session")
        data = {
            "C": "SESSION",
            "app": app,
            "lang": lang,
            "params": params,
        }
        message = serializer.encode(data)
        await self.connection.send(message)

    @typing.overload
    def __init__(self, session_id: str, ws: web.WebSocketResponse, app: str, lang: list[str], params: dict[str, str]): ...

    def __init__(self, *args):
        self.args = args
        self.last_touch = datetime.now()

    async def __aenter__(self):
        from ..session import Session

        logger.debug("Connecting to task processor")
        self.open_connection(self.args[0] + '/' + self.args[2])
        await Session.remind_errors_client(self.args[1])
        self.bind_to_websocket(self.args[1])
        await self.connect_session(self.args[0], self.args[2], self.args[3], self.args[4])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_connection()
