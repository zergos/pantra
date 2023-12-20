import os
import asyncio
from dataclasses import dataclass

import zmq
import zmq.asyncio as zmqa

from ..settings import config
from .base import BaseWorkerClient, BaseWorkerServer


class WorkerServer(BaseWorkerServer):
    @dataclass
    class Listener(BaseWorkerServer.Listener):
        socket: zmqa.Socket

        async def send(self, session_id: str, message: bytes):
            await self.socket.send_multipart([session_id.encode(), message])

        async def receive(self) -> tuple[str, bytes]:
            session_id, message = await self.socket.recv_multipart()
            return session_id.decode(), message

        def close(self):
            self.socket.close()

    def start_listener(self):
        context = zmqa.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind(config.ZMQ_LISTEN)
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
        socket.connect(config.ZMQ_HOST)
        self.connection = WorkerClient.Connection(socket)
