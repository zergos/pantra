from __future__ import annotations

import time
from concurrent import futures
import functools
import threading
import traceback
import typing
import uuid
from queue import Queue
from collections import defaultdict
import logging
from datetime import datetime

from starlette.websockets import WebSocket

from .protocol import Messages
from .settings import config
from .common import UniNode, raise_exception_in_thread, UniqueNode
from .patching import wipe_logger
from .compiler import exec_restart
from .workers.decorators import async_worker
from .trans import get_locale, get_translation, zgettext, Translations
from .session_storage import SessionStorage
from .components.shot import ContextShot

if typing.TYPE_CHECKING:
    from typing import Self, ClassVar, Optional, Any, Callable, Coroutine
    from pathlib import Path

    from .components.context import Context, HTMLElement
    from .components.render.render_node import RenderNode
    from .workers.base import BaseWorkerServer
    from .trans.locale import Locale

logger = logging.getLogger("pantra.system")

class SessionTask(typing.NamedTuple):
    task: threading.Thread | futures.Future
    func: typing.Callable


def trace_errors(func: Callable[[Session, ...], None]):
    @functools.wraps(func)
    def res(session, *args, **kwargs):
        dont_refresh = kwargs.pop("dont_refresh", False)
        if type(session) is not Session:
            raise RuntimeError('trace_errors() wrong call: `session` must be provided')
        try:
            func(session, *args, **kwargs)
        except:
            session.error(traceback.format_exc())
        else:
            if not dont_refresh:
                session.send_shot()
        finally:
            session.send_task_done()
    res.call = func
    return res

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


@wipe_logger
class Session:
    pending_errors: ClassVar[Queue[str]] = Queue()
    states: ClassVar[dict[str, dict[str, Any]]] = defaultdict(dict)
    sessions: ClassVar[dict[str, Self]] = dict()
    server_worker: ClassVar[BaseWorkerServer | None] = None

    __slots__ = ['session_id', 'just_connected', 'state', 'root', 'app', 'user', 'title',
                 'locale', 'translations', 'storage', 'last_touch', 'finish_flag', 'params', 'tasks', '_in_node',
                 '_flicker_next_time']

    @classmethod
    async def run_server_worker(cls):
        cls.server_worker = config.WORKER_SERVER()
        cls.server_worker.start_task_workers()
        cls.server_worker.start_listener()
        await cls.server_worker.run_processor()

    def __new__(cls, session_id: str, app: str, lang: list[str], params: dict[str, str]):
        key = f'{session_id}'
        if key in cls.sessions:
            logger.debug(f"Reuse session {key}")
            cls.sessions[key].params = params
            return cls.sessions[key]
        logger.debug(f"New session {key}")
        self = super().__new__(cls)
        cls.sessions[key] = self
        return self

    def __init__(self, session_id: str, app: str, lang: list[str], params: dict[str, str]):
        self.session_id = session_id
        self.app: str = app
        self.params: dict[str, str] = params
        self.storage: SessionStorage | None = None
        self.last_touch: datetime = datetime.now()
        self.finish_flag: bool = False
        self.tasks: dict[str, SessionTask] = {}

        self.locale: Locale | None = None
        self.translations: Translations | None = None
        self._in_node: RenderNode | None = None
        self._flicker_next_time: int = 0
        if not hasattr(self, "state"):
            self.state: dict[str, Any] = {} # Session.states['browser_id']
            self.just_connected: bool = True
            self.root: Optional[Context] = None
            self.title = ''
            self.user: Optional[dict[str, Any]] = None
            self.set_locale(lang)

    def __getitem__(self, item):
        return self.state[item]

    def __setitem__(self, key, value):
        self.state[key] = value

    def __contains__(self, item):
        return item in self.state

    @staticmethod
    def gen_session_id() -> str:
        return uuid.uuid4().hex

    def restart(self):
        from .components.context import Context
        logger.debug(f"{{{self.app}}} Going to restart...")
        self.send_message(Messages.restart())
        shot = ContextShot()
        ctx = Context("Main", shot=shot, session=self)
        if ctx.template:
            self.root = ctx
            logger.debug(f"{{{self.app}}} Build [Main] context")
            run_safe(self, ctx.renderer.build)

    @async_worker
    async def send_message(self, message: dict[str, Any]):
        from .serializer import serializer
        try:
            code = serializer.encode(message)
        except Exception as e:
            await self.send_message(Messages.error(str(e)))
            return
        self.last_touch = datetime.now()
        await self.server_worker.listener.send(self.session_id, code)

    def node_context(self, node: RenderNode):
        class CtxClass:
            def __enter__(self):
                node.context.session._in_node = node
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    node.context.session._in_node = None
        return CtxClass()

    def error(self, text: str):
        if self._in_node is not None:
            text = f'Error in: {self._in_node.path()}\n{text}'
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
    async def remind_errors_client(cls, ws: WebSocket):
        from .serializer import serializer

        while not cls.pending_errors.empty():
            text = cls.pending_errors.get()
            data = serializer.encode(Messages.error(text))
            await ws.send_bytes(data)

    #async def recover_messages(self):
    #    while not self.pending_messages.empty():
    #        await self.server_worker.listener.send(self.session_id, self.pending_messages.get())

    def send_context(self, ctx: Context):
        return self.send_message(Messages.send_context(ctx))

    @async_worker
    async def send_shot(self):
        if not self.root.shot:
            logger.error('Shot is not prepared yet')
            return

        shot: ContextShot = self.root.shot
        flickering, created, updated, deleted = shot.pop()

        this_time = time.perf_counter()
        has_changes = created or updated or deleted

        if flickering:
            if has_changes or this_time >= self._flicker_next_time:
                self._flicker_next_time = this_time + 1 / config.SHOTS_PER_SECOND
                logger.debug(f"{{{self.app}}} Sending flickering:{len(flickering)}")
                await self.send_message(Messages.update(flickering))

        if not has_changes:
            return
        logger.debug(f"{{{self.app}}} Sending shot NEW:{len(created)} UPD:{len(updated)} DEL:{len(deleted)}")
        if deleted:
            await self.send_message(Messages.delete(deleted))
        if updated:
            await self.send_message(Messages.update(updated))
        if created:
            await self.send_message(Messages.update(created))

    def _collect_children(self, children: list[UniNode], lst: list[UniNode]):
        for child in children:  # type: RenderNode
            if not child:
                continue
            if not child.render_this_node:
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

    def kill_task(self, task_name: str):
        logger.debug(f"{{{self.app}}} Killing task {task_name}")
        if (stask:=self.tasks.get(task_name, None)) is not None:
            if isinstance(stask.task, threading.Thread):
                if stask.task.is_alive():
                    raise_exception_in_thread(stask.task.native_id)
                del self.tasks[task_name]
            elif isinstance(stask.task, futures.Future):
                if not stask.task.cancelled():
                    stask.task.cancel()
            else:
                raise RuntimeError('Unknown task type')
            if hasattr(stask.func, "on_kill"):
                try:
                    stask.func.on_kill()
                except:
                    self.error(traceback.format_exc())
                else:
                    self.send_shot()

    def kill_all_tasks(self, ctx: UniqueNode = None):
        for task_name, stask in list(self.tasks.items()):
            if not isinstance(stask.task, threading.Thread) \
                or isinstance(stask.task, threading.Thread) and stask.task != threading.current_thread():
                if ctx and not task_name.startswith(f'{ctx.oid}#'):
                    continue
                self.kill_task(task_name)

    def request_metrics(self, node: RenderNode):
        logger.debug(f"{{{self.app}}} Request metrics for {node}")
        self.send_message(Messages.request_metrics(node.oid))

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
        dirs = [app.name for app in config.APPS_PATH.glob("*") if app.is_dir() and app.joinpath('Main.html').exists()]
        return dirs

    def start_app(self, app: str):
        logger.debug(f"{{{self.app}}} Start app")
        return self.send_message(Messages.start_app(app))

    def send_title(self, title: str):
        return self.send_message(Messages.set_title(title))

    def set_title(self, title: str):
        self.title = title
        return self.send_title(title)

    def send_task_done(self):
        return self.send_message(Messages.task_done())

    def set_locale(self, lang: str | list):
        lang_name = lang if isinstance(lang, str) else lang[0]
        logger.debug(f"{{{self.app}}} Set lang = {lang_name}")
        self.locale = get_locale(lang_name)
        self.translations = get_translation(self.app, lang)

    def add_translation(self, app: str):
        app_path = config.APPS_PATH / app
        self.translations.merge(Translations.load(app_path / 'locale', (self.locale.language, 'en')))

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

