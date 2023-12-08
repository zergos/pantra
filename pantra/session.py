from __future__ import annotations

import functools
import traceback
import typing
import uuid
from queue import Queue
from collections import defaultdict
import logging

from .settings import config
from .common import ADict, UniNode
from .patching import wipe_logger
from .compiler import exec_restart
from .workers import async_worker
from .trans import get_locale, get_translation, zgettext
from .session_storage import SessionStorage

if typing.TYPE_CHECKING:
    from aiohttp import web
    from .components.context import Context, ContextShot, RenderNode, HTMLElement, AnyNode
    from pathlib import Path
    from typing import *


logger = logging.getLogger("pantra.system")


@wipe_logger
class Session:
    states: ClassVar[dict[str, ADict]] = defaultdict(ADict)
    sessions: ClassVar[dict[str, Self]] = dict()
    pending_errors: Queue[str] = Queue()

    __slots__ = ['state', 'just_connected', 'root', 'app', 'metrics_stack', 'pending_messages', 'ws', 'user', 'title',
                 'locale', 'translations', 'storage']

    def __new__(cls, browser_id: str, session_id: str, ws: web.WebSocketResponse, app: str, lang: str):
        key = f'{session_id}/{app}'
        if key in cls.sessions:
            logger.debug(f"Reuse session {key}")
            return cls.sessions[key]
        logger.debug(f"New session {key}")
        self = super().__new__(cls)
        cls.sessions[key] = self
        return self

    def __init__(self, browser_id: str, session_id: str, ws: web.WebSocketResponse, app: str, lang: List):
        self.app: Optional[str] = app
        self.ws: web.WebSocketResponse = ws
        self.storage: SessionStorage | None = None
        if not hasattr(self, "state"):
            self.state: ADict = ADict() # Session.states['browser_id']
            self.just_connected: bool = True
            self.root: Optional[Context] = None
            self.title = ''
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
    def app_path(self) -> Path:
        if self.app == 'Core':
            return config.COMPONENTS_PATH
        else:
            return config.APPS_PATH / self.app

    @staticmethod
    def gen_session_id() -> str:
        return uuid.uuid4().hex

    def restart(self):
        from .components.render import ContextShot
        from .components.context import Context
        logger.debug(f"{{{self.app}}} Going to restart...")
        self.send_message({'m': 'rst'})
        shot = ContextShot()
        try:
            ctx = Context("Main", shot=shot, session=self)
            if ctx.template:
                self.root = ctx
                logger.debug(f"{{{self.app}}} Build [Main] context")
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
        return self.send_message({'m': 'e', 'l': error})

    @staticmethod
    def error_later(message):
        print(f'Evaluation error: {message}')
        Session.pending_errors.put(message)

    async def remind_errors(self):
        while not Session.pending_errors.empty():
            error = Session.pending_errors.get()
            await self.send_message({'m': 'e', 'l': error})

    async def recover_messages(self):
        while not self.pending_messages.empty():
            await self.ws.send_bytes(self.pending_messages.get())

    def send_context(self, ctx: Context):
        return self.send_message({'m': 'c', 'l': ctx})

    @async_worker
    async def send_shot(self):
        if not self.root.shot:
            logger.error('Shot not prepared yet')
            return
        shot: ContextShot = self.root.shot
        updated, deleted = shot.pop()
        logger.debug(f"{{{self.app}}} Sending shot UPD:{len(updated)} DEL:{len(deleted)}")
        #if ENABLE_LOGGING:
        #    import traceback
        #    logger.debug(''.join(traceback.format_stack(limit=3)))
        if deleted:
            await self.send_message({'m': 'd', 'l': deleted})
        if updated:
            await self.send_message({'m': 'u', 'l': updated})

    def _collect_children(self, children: List[UniNode], lst: List[UniNode]):
        for child in children:  # type: AnyNode
            if not child:
                continue
            if not child.render_this:
                pass
            else:
                lst.append(child)
            self._collect_children(child.children, lst)

    def send_root(self):
        logger.debug(f"{{{self.app}}} Sending root")
        lst = []
        if 'on_restart' in self.root.locals:
            exec_restart(self.root)
        self._collect_children([self.root], lst)
        return self.send_message({'m': 'u', 'l': lst})

    def request_metrics(self, node: RenderNode):
        logger.debug(f"{{{self.app}}} Request metrics for {node}")
        self.send_message({'m': 'm', 'l': node.oid})

    def drop_metrics(self):
        for node in self.metrics_stack:
            if hasattr(node, '_metrics'):
                delattr(node, '_metrics')

    def request_value(self, node: HTMLElement, t: str = 'text'):
        logger.debug(f"{{{self.app}}} Request value for {node}")
        self.send_message({'m': 'v', 'l': node.oid, 't': t})

    def request_validity(self, node: HTMLElement):
        logger.debug(f"{{{self.app}}} Request validity for {node}")
        self.send_message({'m': 'valid', 'l': node.oid})

    def log(self, message):
        return self.send_message({'m': 'log', 'l': message})

    def call(self, method: str, *args):
        logger.debug(f"{{{self.app}}} Calling method {method}")
        return self.send_message({'m': 'call', 'method': method, 'args': args})

    @staticmethod
    def get_apps() -> list[str]:
        dirs = [app.name for app in config.APPS_PATH.glob("*")]
        return dirs

    def start_app(self, app):
        logger.debug(f"{{{self.app}}} Start app")
        return self.send_message({'m': 'app', 'l': app})

    def send_title(self, title):
        return self.send_message({'m': 'title', 'l': title})

    def set_title(self, title):
        self.title = title
        return self.send_title(title)

    def set_locale(self, lang: Union[str, List]):
        lang_name = lang if isinstance(lang, str) else lang[0]
        logger.debug(f"{{{self.app}}} Set lang = {lang_name}")
        self.locale = get_locale(lang_name)
        self.translations = get_translation(self.app_path, lang)

    @typing.overload
    def gettext(self, message: str, *, plural: str = None, n: int = None, ctx: str = None, many: bool = False): ...

    def gettext(self, message: str, **kwargs) -> str:
        return zgettext(self.translations, message, **kwargs)

    def set_storage(self, storage_cls: type[SessionStorage] | SessionStorage):
        from inspect import isclass
        self.storage = storage_cls(self) if isclass(storage_cls) else storage_cls
        self.storage.load()

    def bind_state(self, name: str, dict_ref: dict, key: str = "value"):
        if not self.storage:
            return
        self.storage.add_binding(name, dict_ref, key)

    def bind_states(self, bindings: dict[str, dict | tuple[dict, str]]):
        if not self.storage:
            return
        for k, v in bindings.items():
            if type(v) is tuple:
                self.bind_state(k, *v)
            else:
                self.bind_state(k, v)

    def sync_storage(self):
        if not self.storage:
            return
        self.storage.gather()
        self.storage.dump()

    def key_events_off(self):
        self.send_message({"m": "koff"})

    def key_events_on(self):
        self.send_message({"m": "kon"})


def trace_errors(func: Callable[[Session, ...], None]):
    @functools.wraps(func)
    def res(*args, **kwargs):
        dont_refresh = kwargs.pop("dont_refresh", False)
        if type(args[0]) is not Session:
            return
        try:
            func(*args, **kwargs)
        except:
            args[0].error(traceback.format_exc())
        else:
            if not dont_refresh:
                args[0].send_shot()
    res.call = func
    return res


async def check():
    pass


def trace_errors_async(session: Session, func: Coroutine):
    async def res():
        if session is None:
            raise ValueError('No `session` specified')
        try:
            await func
        except:
            await session.error(traceback.format_exc())
    return res()


@typing.overload
def run_safe(session: Session, func: Callable, *args, dont_refresh: bool = False, **kwargs): ...


@trace_errors
def run_safe(session: Session, func: Callable, *args, **kwargs):
    func(*args, **kwargs)

