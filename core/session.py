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


class Session:
    sessions: Dict[str, 'Session'] = dict()

    def __new__(cls, session_id: str, *args, **kwargs):
        if session_id in cls.sessions:
            return cls.sessions[session_id]
        self = super().__new__(cls)
        cls.sessions[session_id] = self
        return self

    def __init__(self, session_id: str, ws: web.WebSocketResponse, app: Optional[str] = None):
        if not hasattr(self, "state"):
            self.state: AttrDict = AttrDict()
        self.root: Context
        self.ws: web.WebSocketResponse = ws
        self.app: Optional[str] = app
        self.metrics_stack: List[HTMLElement] = []

    @staticmethod
    def gen_session_id():
        return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(8))

    @async_worker
    async def send_message(self, message: Dict['str', Any]):
        from core.serializer import serializer
        await self.ws.send_bytes(serializer.encode(message))

    def error(self, error: str):
        self.send_message({'m': 'e', 'l': error})

    def send_context(self, ctx: Context):
        self.send_message({'m': 'c', 'l': ctx})

    def send_shot(self, shot: ContextShot):
        if shot.deleted:
            self.send_message({'m': 'd', 'l': list(shot.deleted)})
        if shot.updated:
            self.send_message({'m': 'u', 'l': shot.rendered})
        shot.reset()

    def request_metrics(self, node: AnyNode):
        self.send_message({'m': 'm', 'l': node.oid})

    def drop_metrics(self):
        for node in self.metrics_stack:
            if hasattr(node, '_metrics'):
                delattr(node, '_metrics')

    def request_value(self, node: AnyNode):
        self.send_message({'m': 'v', 'l': node.oid})

    def log(self, message):
        self.send_message({'m': 'log', 'l': message})


def trace_errors(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            args[0].session.error(traceback.format_exc())
        else:
            args[0].session.send_shot(args[0].shot)
    res.call = func
    return res
