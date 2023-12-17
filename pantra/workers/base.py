from __future__ import annotations

import asyncio
import typing
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
import threading
import queue

from ..common import raise_exception_in_thread
from ..settings import config
from ..patching import wipe_logger

if typing.TYPE_CHECKING:
    from aiohttp import web
    from ..session import Session

logger = logging.getLogger('pantra.system')

@dataclass
class WorkerStat:
    active: bool = False
    last_time: float = 0
    finish_flag: int = 0


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

    listener: Listener
    async_loop: asyncio.AbstractEventLoop

    def task_processor(self):
        try:
            ident = threading.current_thread().name
            if ident not in BaseWorkerServer.workers:
                BaseWorkerServer.workers[ident] = WorkerStat()
            while True:
                try:
                    func, args, kwargs = BaseWorkerServer.task_queue.get(timeout=5)
                except queue.Empty:
                    if BaseWorkerServer.workers[ident].finish_flag:
                        BaseWorkerServer.workers[ident].finish_flag = -1
                        break
                    continue
                if func is None: break
                BaseWorkerServer.workers[ident].last_time = time.perf_counter()
                BaseWorkerServer.workers[ident].active = True
                func(*args, **kwargs)
                BaseWorkerServer.workers[ident].last_time = time.perf_counter()
                BaseWorkerServer.workers[ident].active = False
        except SystemExit:
            logger.error(f'`{ident}` thread got exit signal')

    def tasks_controller(self):
        while True:
            time.sleep(1)
            tick = time.perf_counter()
            last_tick = 0
            if len(BaseWorkerServer.workers) > config.MIN_TASK_THREADS:
                for k, v in list(BaseWorkerServer.workers.items()):  # type: str, WorkerStat
                    if v.finish_flag != 0:
                        if v.finish_flag == -1:
                            logger.warning(f"Thread killed `f{k}`")
                            del BaseWorkerServer.workers[k]
                        continue
                    if v.active and tick - v.last_time > config.THREAD_TIMEOUT:
                        if len(BaseWorkerServer.workers) > config.MIN_TASK_THREADS:
                            logger.warning(f"Thread removing `f{k}`")
                            raise_exception_in_thread(k)
                            del BaseWorkerServer.workers[k]
                    elif v.last_time and not v.active and tick - v.last_time > config.KILL_THREAD_LAG:
                        logger.warning(f"Thread killing `f{k}`")
                        v.finish_flag = 1
                    if tick > last_tick:
                        last_tick = tick
            if not BaseWorkerServer.task_queue.empty() and last_tick and tick - last_tick > config.CREAT_THREAD_LAG:
                logger.warning(f'New thread creation X#{len(BaseWorkerServer.workers)}')
                threading.Thread(target=self.task_processor, name=f'X#{len(BaseWorkerServer.workers)}').start()

    def start_task_workers(self):
        logger.debug("Starting task workers")
        BaseWorkerServer.task_queue = queue.Queue()
        for i in range(config.MIN_TASK_THREADS):
            threading.Thread(target=self.task_processor, name=f'#{i}', daemon=True).start()
        threading.Thread(target=self.tasks_controller, daemon=True).start()

    @abstractmethod
    def start_listener(self): ...

    async def run_processor(self):
        from ..session import Session
        from ..serializer import serializer
        from ..protocol import process_message

        logger.debug("Starting task processor")

        self.async_loop = asyncio.get_running_loop()

        session: Session = None
        while True:
            session_id, message = await self.listener.receive()
            data = serializer.decode(message)

            if data['C'] == "SESSION":
                session = Session(session_id, data['app'], data['lang'])
            else:
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
                await ws.send_bytes(message)
        self.sync_task = asyncio.create_task(task())

    async def connect_session(self, session_id: str, app: str, lang: list[str]):
        from ..serializer import serializer

        logger.debug("Initiate session")
        data = {
            "C": "SESSION",
            "app": app,
            "lang": lang
        }
        message = serializer.encode(data)
        await self.connection.send(message)

    @typing.overload
    def __init__(self, session_id: str, ws: web.WebSocketResponse, app: str, lang: list[str]): ...

    def __init__(self, *args):
        self.args = args

    async def __aenter__(self):
        from ..session import Session

        logger.debug("Connecting to task processor")
        self.open_connection(self.args[0])
        await Session.remind_errors_client(self.args[1])
        self.bind_to_websocket(self.args[1])
        await self.connect_session(self.args[0], self.args[2], self.args[3])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_connection()