from __future__ import annotations

import os
import random
import string
import functools
import traceback
import typing
import uuid
from queue import Queue

from .defaults import APPS_PATH, COMPONENTS_PATH
from .common import ADict, UniNode
from .compiler import exec_restart
from .workers import async_worker
from .trans import get_locale, get_translation, zgettext

if typing.TYPE_CHECKING:
    from aiohttp import web
    from .components.context import Context, ContextShot, RenderNode, HTMLElement, AnyNode
    from typing import *


class Session:
    sessions: Dict[str, 'Session'] = dict()
    pending_errors: Queue[str] = Queue()

    __slots__ = ['state', 'just_connected', 'root', 'app', 'metrics_stack', 'pending_messages', 'ws', 'user', 'title', 'locale', 'translations']

    def __new__(cls, session_id: str, ws: web.WebSocketResponse, app: str, lang: str):
        key = f'{session_id}/{app}'
        if key in cls.sessions:
            return cls.sessions[key]
        self = super().__new__(cls)
        cls.sessions[key] = self
        return self

    def __init__(self, session_id: str, ws: web.WebSocketResponse, app: str, lang: List):
        self.app: Optional[str] = app
        self.ws: web.WebSocketResponse = ws
        if not hasattr(self, "state"):
            self.state: ADict = ADict()
            self.just_connected: bool = True
            self.root: Optional[Context] = None
            self.title = 'Fruity App'
            self.metrics_stack: List[HTMLElement] = []
            self.pending_messages: Queue[bytes] = Queue()
            self.user: Optional[Dict[str, Any]] = None
            self.set_locale(lang)

    def __getitem__(self, item):
        return self.state[item]

    def __setitem__(self, key, value):
        self.state[key] = value

    def __contains__(self, item):
        return item in self.state

    @property
    def app_path(self):
        if self.app == 'Core':
            return COMPONENTS_PATH
        else:
            return os.path.join(APPS_PATH, self.app)

    @staticmethod
    def gen_session_id():
        return uuid.uuid4().hex

    def restart(self):
        from .components.render import ContextShot
        from .components.context import Context
        self.send_message({'m': 'rst'})
        shot = ContextShot()
        try:
            ctx = Context("Main", shot=shot, session=self)
            if ctx.template:
                self.root = ctx
                ctx.render.build()
                self.send_shot()
        except:
            # print(traceback.format_exc())
            self.error(traceback.format_exc(-3))
        self.remind_errors()

    @async_worker
    async def send_message(self, message: Dict['str', Any]):
        from .serializer import serializer
        if self.ws is None or self.ws.closed:
            self.pending_messages.put(serializer.encode(message))
        else:
            try:
                code = serializer.encode(message)
            except Exception as e:
                print(traceback.format_exc())
            else:
                await self.ws.send_bytes(code)

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
        if not self.root.shot:
            print('Shot not prepared yet')
            return
        shot: ContextShot = self.root.shot
        if shot.deleted:
            self.send_message({'m': 'd', 'l': list(shot.deleted)})
        if shot.updated:
            self.send_message({'m': 'u', 'l': list(shot.updated)})
        shot.reset()

    def _collect_children(self, children: List[UniNode], lst: List[UniNode]):
        for child in children:  # type: AnyNode
            if not child:
                continue
            if not child.render_this:
                pass
            else:
                lst.append(child)
            self._collect_children(child.children, lst)

    async def send_root(self):
        lst = []
        if 'on_restart' in self.root.locals:
            exec_restart(self.root)
        self._collect_children([self.root], lst)
        await self.send_message({'m': 'u', 'l': lst})

    def request_metrics(self, node: RenderNode):
        self.send_message({'m': 'm', 'l': node.oid})

    def drop_metrics(self):
        for node in self.metrics_stack:
            if hasattr(node, '_metrics'):
                delattr(node, '_metrics')

    def request_value(self, node: HTMLElement, t: str = 'text'):
        self.send_message({'m': 'v', 'l': node.oid, 't': t})

    def request_validity(self, node: HTMLElement):
        self.send_message({'m': 'valid', 'l': node.oid})

    def log(self, message):
        self.send_message({'m': 'log', 'l': message})

    @staticmethod
    def get_apps():
        (_, dirs, _) = next(os.walk(APPS_PATH), (None, [], None))
        return dirs

    def start_app(self, app):
        self.send_message({'m': 'app', 'l': app})

    def send_title(self, title):
        return self.send_message({'m': 'title', 'l': title})

    def set_title(self, title):
        self.title = title
        self.send_title(title)

    def set_locale(self, lang: Union[str, List]):
        self.locale = get_locale(lang if isinstance(lang, str) else lang[0])
        self.translations = get_translation(self.app_path, lang)

    @typing.overload
    def gettext(self, message: str, *, plural: str = None, n: int = None, ctx: str = None, many: bool = False): ...

    def gettext(self, message: str, **kwargs) -> str:
        return zgettext(self.translations, message, **kwargs)


def trace_errors(func: Callable[[Session, ...], None]):
    @functools.wraps(func)
    def res(*args, **kwargs):
        if type(args[0]) is not Session:
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
def run_safe(session: Session, func: Callable, *args, **kwargs):
    func(*args, **kwargs)

