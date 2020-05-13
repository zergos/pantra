from __future__ import annotations
import random
import string
import functools
import traceback
from queue import Queue
from typing import *
from aiohttp import web
from attrdict import AttrDict

from core.workers import async_worker
if TYPE_CHECKING:
    from core.components.context import Context, ContextShot, RenderNode, HTMLElement


class Session:
    sessions: Dict[str, 'Session'] = dict()
    pending_errors: Queue[str] = Queue()

    def __new__(cls, session_id: str, *args, **kwargs):
        if session_id in cls.sessions:
            return cls.sessions[session_id]
        self = super().__new__(cls)
        cls.sessions[session_id] = self
        return self

    def __init__(self, session_id: str, ws: web.WebSocketResponse, app: Optional[str] = None):
        if not hasattr(self, "state"):
            self.state: AttrDict = AttrDict()
        self.root: Optional[Context] = None
        self.ws: web.WebSocketResponse = ws
        self.app: Optional[str] = app
        self.metrics_stack: List[HTMLElement] = []
        self.just_connected: bool = True
        self.pending_messages: Queue[bytes] = Queue()

    @staticmethod
    def gen_session_id():
        return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(8))

    @async_worker
    async def send_message(self, message: Dict['str', Any]):
        from core.serializer import serializer
        if not self.ws or self.ws.closed:
            self.pending_messages.put(serializer.encode(message))
        else:
            await self.ws.send_bytes(serializer.encode(message))

    def error(self, error: str):
        self.send_message({'m': 'e', 'l': error})

    @staticmethod
    def error_later(message):
        Session.pending_errors.put(message)

    async def remind_errors(self):
        while not Session.pending_errors.empty():
            error = Session.pending_errors.get()
            await self.send_message({'m': 'e', 'l': error})

    async def recover_messages(self):
        while not self.pending_messages.empty():
            await self.ws.send_bytes(self.pending_messages.get())

    def send_context(self, ctx: Context):
        self.send_message({'m': 'c', 'l': ctx})

    def send_shot(self, shot: ContextShot):
        if shot.deleted:
            self.send_message({'m': 'd', 'l': list(shot.deleted)})
        if shot.updated:
            self.send_message({'m': 'u', 'l': shot.rendered})
        shot.reset()

    def request_metrics(self, node: RenderNode):
        self.send_message({'m': 'm', 'l': node.oid})

    def drop_metrics(self):
        for node in self.metrics_stack:
            if hasattr(node, '_metrics'):
                delattr(node, '_metrics')

    def request_value(self, node: RenderNode):
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
