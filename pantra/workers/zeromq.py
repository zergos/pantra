import os
import asyncio
from dataclasses import dataclass

import zmq
import zmq.asyncio as zmqa

from ..settings import config
from . import BaseWorkerClient, BaseWorkerServer


class WorkerServer(BaseWorkerServer):
    @dataclass
    class Listener(BaseWorkerServer.Listener):
        socket: zmqa.Socket

        async def send(self, session_id: str, message: bytes):
            await self.socket.send_multipart([session_id, message])

        async def receive(self) -> tuple[str, bytes]:
            session_id, message = await self.socket.recv_multipart()
            return session_id, message

        def close(self):
            self.socket.close()

    def start_listener(self):
        context = zmqa.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind(f'tcp://*:{config.ZMQ_PORT}')
        self.listener = WorkerServer.Listener(socket)


class WorkerClient(BaseWorkerClient):
    @dataclass
    class Connection(BaseWorkerClient.Connection):
        socket: zmqa.Socket

        async def send(self, message: bytes):
            await self.socket.send(message)

        async def receive(self) -> bytes:
            return await self.socket.recv()

        def close(self):
            self.socket.close()


    def open_connection(self, session_id: str):
        context = zmqa.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY, session_id.encode())
        socket.connect(f"tcp://{config.ZMQ_HOST}:{config.ZMQ_PORT}")
        self.connection = WorkerClient.Connection(socket)
