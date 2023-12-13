from __future__ import annotations

import functools
import traceback
import typing
import uuid
from queue import Queue
from collections import defaultdict
import logging

from aiohttp import web

from .protocol import Messages
from .settings import config
from .common import ADict, UniNode
from .patching import wipe_logger
from .compiler import exec_restart
from .workers.decorators import async_worker
from .trans import get_locale, get_translation, zgettext
from .session_storage import SessionStorage

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import *

    from .components.context import Context, ContextShot, RenderNode, HTMLElement, AnyNode
    from .workers import BaseWorkerServer


logger = logging.getLogger("pantra.system")

@wipe_logger
class Session:
    pending_errors: ClassVar[Queue[str]] = Queue()
    states: ClassVar[dict[str, ADict]] = defaultdict(ADict)
    sessions: ClassVar[dict[str, Self]] = dict()
    server_worker: ClassVar[BaseWorkerServer] = None

    __slots__ = ['session_id', 'just_connected', 'state', 'root', 'app', 'metrics_stack', 'user', 'title',
                 'locale', 'translations', 'storage']

    @classmethod
    async def run_server_worker(cls):
        cls.server_worker = config.WORKER_SERVER()
        cls.server_worker.start_task_workers()
        cls.server_worker.start_listener()
        await cls.server_worker.run_processor()

    def __new__(cls, session_id: str, app: str, lang: list[str]):
        key = f'{session_id}/{app}'
        if key in cls.sessions:
            logger.debug(f"Reuse session {key}")
            return cls.sessions[key]
        logger.debug(f"New session {key}")
        self = super().__new__(cls)
        cls.sessions[key] = self
        return self

    def __init__(self, session_id: str, app: str, lang: list[str]):
        self.session_id = session_id
        self.app: Optional[str] = app
        self.storage: SessionStorage | None = None
        if not hasattr(self, "state"):
            self.state: ADict = ADict() # Session.states['browser_id']
            self.just_connected: bool = True
            self.root: Optional[Context] = None
            self.title = ''
            self.metrics_stack: list[HTMLElement] = []
            self.user: Optional[dict[str, Any]] = None
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
        self.send_message(Messages.restart())
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

    @async_worker
    async def send_message(self, message: dict[str, Any]):
        from .serializer import serializer

        try:
            code = serializer.encode(message)
        except:
            logger.error(traceback.format_exc())
        else:
            await self.server_worker.listener.send(self.session_id, code)

    def error(self, text: str):
        return self.send_message(Messages.error(text))

    @staticmethod
    def error_later(message):
        logger.error(f'Evaluation error: {message}')
        Session.pending_errors.put(message)

    async def remind_errors(self):
        while not Session.pending_errors.empty():
            text = Session.pending_errors.get()
            await self.send_message(Messages.error(text))

    @classmethod
    async def remind_errors_client(cls, ws: web.WebSocketResponse):
        from .serializer import serializer

        while not cls.pending_errors.empty():
            text = cls.pending_errors.get()
            data = serializer.encode(Messages.error(text))
            await ws.send_bytes(data)

    async def recover_messages(self):
        while not self.pending_messages.empty():
            await self.server_worker.listener.send(self.session_id, self.pending_messages.get())

    def send_context(self, ctx: Context):
        return self.send_message(Messages.send_context(ctx))

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
            await self.send_message(Messages.delete(deleted))
        if updated:
            await self.send_message(Messages.update(updated))

    def _collect_children(self, children: list[UniNode], lst: list[UniNode]):
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
        return self.send_message(Messages.update(lst))

    def request_metrics(self, node: RenderNode):
        logger.debug(f"{{{self.app}}} Request metrics for {node}")
        self.send_message(Messages.request_metrics(node.oid))

    def drop_metrics(self):
        for node in self.metrics_stack:
            if hasattr(node, '_metrics'):
                delattr(node, '_metrics')

    def request_value(self, node: HTMLElement, typ: str = 'text'):
        logger.debug(f"{{{self.app}}} Request value for {node}")
        self.send_message(Messages.request_value(node.oid, typ))

    def request_validity(self, node: HTMLElement):
        logger.debug(f"{{{self.app}}} Request validity for {node}")
        self.send_message(Messages.request_validity(node.oid))

    def log(self, text: str):
        return self.send_message(Messages.log(text))

    def call(self, method: str, *args):
        logger.debug(f"{{{self.app}}} Calling method {method}")
        return self.send_message(Messages.call(method, args))

    @staticmethod
    def get_apps() -> list[str]:
        dirs = [app.name for app in config.APPS_PATH.glob("*")]
        return dirs

    def start_app(self, app: str):
        logger.debug(f"{{{self.app}}} Start app")
        return self.send_message(Messages.start_app(app))

    def send_title(self, title: str):
        return self.send_message(Messages.set_title(title))

    def set_title(self, title: str):
        self.title = title
        return self.send_title(title)

    def set_locale(self, lang: Union[str, list]):
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
        self.send_message(Messages.keys_off())

    def key_events_on(self):
        self.send_message(Messages.keys_on())


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
        else:
            await session.send_shot()
    return res()


@typing.overload
def run_safe(session: Session, func: Callable, *args, dont_refresh: bool = False, **kwargs): ...


@trace_errors
def run_safe(session: Session, func: Callable, *args, **kwargs):
    func(*args, **kwargs)

