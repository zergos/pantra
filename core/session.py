from __future__ import annotations
import random
import string
import functools
import traceback
from typing import *
from aiohttp import web
from attrdict import AttrDict

from core.workers import async_worker
if TYPE_CHECKING:
    from core.components.context import Context, ContextShot, AnyNode, HTMLElement
    from core.serializer import serializer


class Session:
    sessions: Dict[str, 'Session'] = dict()

    def __new__(cls, session_id: str, *args, **kwargs):
        if session_id in cls.sessions:
            return cls.sessions[session_id]
        self = super().__new__(cls)
        cls.sessions[session_id] = self
        return self

    def __init__(self, session_id: str, ws: web.WebSocketResponse):
        if not hasattr(self, "state"):
            self.state: AttrDict = AttrDict()
        self.root: Context
        self.ws: web.WebSocketResponse = ws
        self.metrics_stack: List[HTMLElement] = []

    @staticmethod
    def gen_session_id():
        return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(8))

    @async_worker
    async def send_message(self, message: Dict['str', Any]):
        from core.serializer import serializerU
        await self.ws.send_bytes(serializerU.encode(message))

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

    def drop_metrics(self):
        for node in self.metrics_stack:
            if hasattr(node, '_metrics'):
                delattr(node, '_metrics')


def trace_errors(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            args[0].session.send_error(traceback.format_exc())
        else:
            args[0].session.send_shot(args[0].shot)
    return res
