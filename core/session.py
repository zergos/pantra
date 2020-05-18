from __future__ import annotations

import os
import random
import string
import functools
import traceback
from queue import Queue
from typing import *
from aiohttp import web

from core.common import ADict, UniNode, typename
from core.workers import async_worker
from defaults import APPS_PATH

if TYPE_CHECKING:
    from core.components.context import Context, ContextShot, RenderNode, HTMLElement, AnyNode


class Session:
    sessions: Dict[str, 'Session'] = dict()
    pending_errors: Queue[str] = Queue()

    __slots__ = ['state', 'just_connected', 'root', 'app', 'metrics_stack', 'pending_messages', 'ws', 'user']

    def __new__(cls, session_id: str, ws: web.WebSocketResponse, app: Optional[str] = None):
        key = f'{session_id}/{app}'
        if key in cls.sessions:
            return cls.sessions[key]
        self = super().__new__(cls)
        cls.sessions[key] = self
        return self

    def __init__(self, session_id: str, ws: web.WebSocketResponse, app: Optional[str] = None):
        if not hasattr(self, "state"):
            self.state: ADict = ADict()
            self.just_connected: bool = True
            self.root: Optional[Context] = None
            self.metrics_stack: List[HTMLElement] = []
            self.pending_messages: Queue[bytes] = Queue()
            self.user: Optional[Dict[str, Any]] = None
        self.app: Optional[str] = app
        self.ws: web.WebSocketResponse = ws

    @staticmethod
    def gen_session_id():
        return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(8))

    def restart(self):
        from core.components.render import ContextShot
        from core.components.context import Context
        self.send_message({'m': 'rst'})
        shot = ContextShot()
        try:
            ctx = Context("Main", shot=shot, session=self)
            if ctx.template:
                self.root = ctx
                ctx.render.build()
                self.send_shot()
        except Exception as e:
            print(traceback.format_exc())
        self.remind_errors()

    @async_worker
    async def send_message(self, message: Dict['str', Any]):
        from core.serializer import serializer
        if self.ws is None or self.ws.closed:
            self.pending_messages.put(serializer.encode(message))
        else:
            await self.ws.send_bytes(serializer.encode(message))

    def error(self, error: str):
        self.send_message({'m': 'e', 'l': error})

    @staticmethod
    def error_later(message):
        print(f'Evaluation error: {message}')
        Session.pending_errors.put(message)

    @async_worker
    async def remind_errors(self):
        while not Session.pending_errors.empty():
            error = Session.pending_errors.get()
            await self.send_message({'m': 'e', 'l': error})

    async def recover_messages(self):
        while not self.pending_messages.empty():
            await self.ws.send_bytes(self.pending_messages.get())

    def send_context(self, ctx: Context):
        self.send_message({'m': 'c', 'l': ctx})

    def send_shot(self):
        shot: ContextShot = self.root.shot
        if shot.deleted:
            self.send_message({'m': 'd', 'l': list(shot.deleted)})
        if shot.updated:
            self.send_message({'m': 'u', 'l': shot.rendered})
        shot.reset()

    def _collect_children(self, children: List[UniNode], lst: List[UniNode]):
        for child in children:  # type: AnyNode
            if not child:
                continue
            if not child.render_this or typename(child) == 'Context' and not child.render_base:
                pass
            else:
                lst.append(child)
            self._collect_children(child.children, lst)

    async def send_root(self):
        lst = []
        self._collect_children([self.root], lst)
        await self.send_message({'m': 'u', 'l': lst})

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

    @staticmethod
    def get_apps():
        (_, dirs, _) = next(os.walk(APPS_PATH), (None, [], None))
        return dirs

    def start_app(self, app):
        self.send_message({'m': 'app', 'l': app})


def trace_errors(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        if args[0] is None:
            return
        try:
            func(*args, **kwargs)
        except:
            args[0].error(traceback.format_exc())
        else:
            args[0].send_shot()
    res.call = func
    return res


@trace_errors
def run_safe(ctx: Context, func: Callable, *args, **kwargs):
    func(*args, **kwargs)

