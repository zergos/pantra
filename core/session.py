import random
import string
from typing import *
from aiohttp import web
from attrdict import AttrDict

from core.components.context import Context, ContextShot, AnyNode
from core.serializer import serializer
from core.workers import async_worker


class Session:
    sessions: Dict[str, 'Session']

    def __new__(cls, session_id: str, *args, **kwargs):
        if session_id in cls.sessions:
            return cls.sessions[session_id]
        self = super().__new__(cls)
        cls.sessions[session_id] = self
        return self

    def __init__(self, session_id: str, ws: web.WebSocketResponse):
        if not hasattr(self, "data"):
            self.data: AttrDict = AttrDict()
        self.root: Context
        self.ws: web.WebSocketResponse = ws

    @staticmethod
    def gen_session_id():
        return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(8))

    @async_worker
    async def send_message(self, message: Dict['str', Any]):
        await self.ws.send_bytes(serializer.encode(message))

    def send_error(self, error: str):
        self.send_message({'m': 'e', 'l': error})

    def send_context(self, ctx: Context):
        self.send_message({'m': 'c', 'l': ctx})

    def send_shot(self, shot: ContextShot):
        if shot.deleted:
            self.send_message({'m': 'd', 'l': list(shot.deleted)})
        if shot.updated:
            self.send_message({'m': 'u', 'l': shot.updated})
        shot.reset()

    def request_metrics(self, node: AnyNode):
        self.send_message({'m': 'm', 'l': id(node)})
