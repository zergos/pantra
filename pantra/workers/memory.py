import typing
from dataclasses import dataclass

from asyncio.queues import Queue

from .base import BaseWorkerClient, BaseWorkerServer


class WorkerServer(BaseWorkerServer):
    run_with_web: typing.ClassVar[bool] = True

    queue: typing.ClassVar[Queue[tuple[str, bytes]]] = Queue()
    queues: typing.ClassVar[dict[str, Queue[bytes]]] = {}

    class Listener(BaseWorkerServer.Listener):
        async def send(self, session_id: str, message: bytes):
            await WorkerServer.queues[session_id].put(message)

        async def receive(self) -> tuple[str, bytes]:
            session_id, message = await WorkerServer.queue.get()
            return session_id, message

        def close(self):
            pass

    def start_listener(self):
        self.listener = WorkerServer.Listener()


class WorkerClient(BaseWorkerClient):
    @dataclass
    class Connection(BaseWorkerClient.Connection):
        session_id: str
        queue: Queue[bytes]

        async def send(self, message: bytes):
            await WorkerServer.queue.put((self.session_id, message))

        async def receive(self) -> bytes:
            return await self.queue.get()

        def close(self):
            pass


    def open_connection(self, session_id: str):
        queue = Queue()
        WorkerServer.queues[session_id] = queue
        self.connection = WorkerClient.Connection(session_id, queue)
