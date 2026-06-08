from __future__ import annotations

import time
from concurrent import futures
import functools
import threading
import traceback
import typing
import uuid
from queue import Queue
from datetime import datetime
import inspect

from starlette.websockets import WebSocket

from .protocol import Messages
from .settings import config, logger
from .common import UniNode, raise_exception_in_thread, UniqueNode
from .patching import wipe_logger
from .compiler import exec_restart
from .workers.decorators import async_worker
from .trans import get_locale, get_translation, zgettext, Translations
from .session_storage import SessionStorage, NullSessionStorage
from .components.shot import ContextShot

if typing.TYPE_CHECKING:
    from typing import Self, ClassVar, Optional, Any, Callable, Coroutine, Mapping, ContextManager

    from .components.context import Context, HTMLElement, AnyNode
    from .components.shot import ContextShotLike
    from .components.render.render_node import RenderNode
    from .workers.base import BaseWorkerServer
    from .trans.locale import Locale

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
        except SystemExit:
            """The task killed gracefully"""
        except Exception as e:
            session.error(traceback.format_exc(-3), e)
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
        except Exception as e:
            await session.error(traceback.format_exc(-3), e)
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
    """Session class.

    Session is created on new user connection and contains isolated user-related data.

    Attributes:
        session_id: unique session id, generated on client side
        app (str): current application name
        title: application title to the browser page (see :meth:`set_title`)
        user: current user ID, if used
        state (dict[str, Any]): any user-related data, associated with active session
        root (Context): root component (always "Main")
        locale (Locale): current locale (see :meth:`set_locale` and :doc:`more <translation>`)
        storage (SessionStorage): permanent settings storage (see :doc:`more <session_storage>`)
        params (dict[str, str]): URL params (http://localhost/app/?a=1&b=2&c=3)
        last_touch (datetime): last time event was triggered on this session
        tasks (dict[str, SessionTask]): all tasks running (see :doc:`more <session_tasks>`)
        sessions (dict[str, Session]): (class variable) all sessions collection
        pending_errors (Queue[str]): (class variable) all pending errors queue, to send to next user on next session
        server_worker (BaseWorkerServer): (class variable) main server worker to host all sessions
    """
    pending_errors: ClassVar[Queue[str]] = Queue()
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
        self.storage: SessionStorage | None = config.SESSION_STORAGE(self)
        self.last_touch: datetime = datetime.now()
        self.finish_flag: bool = False
        self.tasks: dict[str, SessionTask] = {}

        self._in_node: RenderNode | None = None
        self._flicker_next_time: int = 0
        if not hasattr(self, "state"):
            self.state: dict[str, Any] = {} # Session.states['browser_id']
            self.just_connected: bool = True
            self.root: Optional[Context] = None
            self.title = ''
            self.user: Optional[dict[str, Any]] = None
            self.locale: Locale | None = None
            self.translations: Translations | None = None
            self.set_locale(lang)
            if config.SESSION_STORAGE is not None:
                self.storage: SessionStorage | None = config.SESSION_STORAGE(self)
            else:
                self.storage = NullSessionStorage(self)
        else:
            pass

    def __getitem__(self, item):
        """shortcut to read value from state"""
        return self.state[item]

    def __setitem__(self, key, value):
        """shortcut to set value to state"""
        self.state[key] = value

    def __contains__(self, item):
        """check variable in state"""
        return item in self.state

    @staticmethod
    def gen_session_id() -> str:
        """simple unique session id generator"""
        return uuid.uuid4().hex

    def get_node(self, oid: int) -> AnyNode | None:
        """shortcut to get node by OID (read :doc:`here <js_callback>`)"""
        if not self.root:
            return None
        return self.root.oid_gen.get_node(oid)

    def restart(self):
        """restart application and rebuild main context"""
        from .components.context import Context
        logger.debug(f"{{{self.app}}} Going to restart...")
        self.send_message(Messages.restart())
        shot = ContextShot()
        ctx = Context("Main", shot=shot, session=self)
        if ctx.template:
            self.root: Context = ctx
            logger.debug(f"{{{self.app}}} Build [Main] context")
            run_safe(self, ctx.renderer.build)

    @async_worker
    async def send_message(self, message: dict[str, Any]):
        """send message to client-side using inner protocol

        :meta private:
        """
        from .serializer import serializer
        try:
            code = serializer.encode(message)
        except Exception as e:
            await self.send_message(Messages.error(f'Serialization error: {traceback.format_exc(-3)}'))
            return
        self.last_touch = datetime.now()
        await self.server_worker.listener.send(self.session_id, code)

    @staticmethod
    def node_context(node: RenderNode) -> ContextManager[None]:
        """context manager to extend exception with ref to node

        :meta private:
        """
        class CtxClass:
            __slots__ = ()
            def __enter__(self):
                pass
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    setattr(exc_val, 'node', node)
        return CtxClass()

    def error(self, text: str, exc_value: Exception | None = None):
        """send error message to client-side

        Arguments:
            text: error text
            exc_value: exception value with reference to node
        """
        if exc_value is not None and (node:=getattr(exc_value, "node", None)) is not None:
            text = f'Error in: {node.path()}\n{text}'
        return self.send_message(Messages.error(text))

    @staticmethod
    def error_later(message):
        """collect pending errors outside the active session"""
        logger.error(f'Evaluation error: {message}')
        if not config.PRODUCTIVE:
            Session.pending_errors.put(message)

    async def remind_errors(self):
        """send pending errors to client-side

        :meta private:
        """
        while not Session.pending_errors.empty():
            text = Session.pending_errors.get()
            await self.send_message(Messages.error(text))

    @classmethod
    async def remind_errors_client(cls, ws: WebSocket):
        """send pending errors to client-side via WebSocket directly (frontend part)

        :meta private:
        """
        from .serializer import serializer

        while not cls.pending_errors.empty():
            text = cls.pending_errors.get()
            data = serializer.encode(Messages.error(text))
            await ws.send_bytes(data)

    #async def recover_messages(self):
    #    while not self.pending_messages.empty():
    #        await self.server_worker.listener.send(self.session_id, self.pending_messages.get())

    def send_context(self, ctx: Context):
        """send component context after build (obsolete)

        :meta private:
        """
        return self.send_message(Messages.send_context(ctx))

    @async_worker
    async def send_shot(self):
        """send DOM changes snapshot"""
        if not self.root.shot:
            logger.error('Shot is not prepared yet')
            return

        shot: ContextShotLike = self.root.shot
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

    def resend_root(self):
        """resend root context after page refresh

        :meta private:
        """
        logger.debug(f"{{{self.app}}} Sending root")
        lst = []
        if 'on_restart' in self.root.locals:
            exec_restart(self.root)
        self._collect_children([self.root], lst)
        return self.send_message(Messages.update(lst))

    def kill_task(self, task_name: str):
        """kill :doc:`task <session_tasks>` by name"""
        logger.warning(f"{{{self.app}}} Killing task {task_name}")
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
        """kill all :doc:`tasks <session_tasks>` for specified context and all"""
        for task_name, stask in list(self.tasks.items()):
            if not isinstance(stask.task, threading.Thread) \
                or isinstance(stask.task, threading.Thread) and stask.task != threading.current_thread():
                if ctx and not task_name.startswith(f'{ctx.oid}#'):
                    continue
                self.kill_task(task_name)

    def request_measures(self, node: RenderNode):
        """send message request metrics

        :meta private:
        """
        logger.debug(f"{{{self.app}}} Request measures for {node}")
        self.send_message(Messages.request_measures(node.oid))

    def request_value(self, node: HTMLElement, typ: str = 'text'):
        """send message request value

        :meta private:
        """
        logger.debug(f"{{{self.app}}} Request value for {node}")
        self.send_message(Messages.request_value(node.oid, typ))

    def request_validity(self, node: HTMLElement):
        """send message request validity

        :meta private:
        """
        logger.debug(f"{{{self.app}}} Request validity for {node}")
        self.send_message(Messages.request_validity(node.oid))

    def log(self, text: str):
        """send message to user browser's debug console"""
        return self.send_message(Messages.log(text))

    def call(self, method: str, *args):
        """call JavaScript :doc:`method <js_callback>` by name and arguments"""
        logger.debug(f"{{{self.app}}} Calling method {method}")
        return self.send_message(Messages.call(method, args))

    @staticmethod
    def get_apps() -> list[str]:
        """get list of available apps"""
        dirs = [app.name for app in config.APPS_PATH.glob("*") if app.is_dir() and app.joinpath('Main.html').exists()]
        return dirs

    def start_app(self, app: str):
        """send message to switch to and start app"""
        logger.debug(f"{{{self.app}}} Start app")
        return self.send_message(Messages.start_app(app))

    def send_title(self, title: str):
        """send message to set web page title

        :meta private:
        """
        return self.send_message(Messages.set_title(title))

    def set_title(self, title: str):
        """set title and send to client-side"""
        self.title = title
        return self.send_title(title)

    def send_task_done(self):
        """send signal task finished, to remove waiting (spinner) animation"""
        return self.send_message(Messages.task_done())

    def set_locale(self, lang: str | list):
        """set :doc:`locale <translation>` from one or several languages specified"""
        lang_name = lang if isinstance(lang, str) else lang[0]
        logger.debug(f"{{{self.app}}} Set lang = {lang_name}")
        self.locale = get_locale(lang_name)
        self.translations = get_translation(self.app, lang)

    def load_translation(self, app: str):
        """load translation for specified app

        :meta private:
        """
        app_path = config.APPS_PATH / app
        self.translations.merge(Translations.load(app_path / 'locale', (self.locale.language, 'en')))

    @typing.overload
    def zgettext(self, message: str, *args, plural: str = None, n: int = None, ctx: str = None, many: bool = False): ...

    def zgettext(self, message: str, *args, **kwargs) -> str:
        """unite :doc:`translation <translation>` function"""
        return zgettext(self.translations, message, *args, **kwargs)

    def gettext(self, message: str) -> str:
        """simple :doc:`translation <translation>` function"""
        return self.translations.gettext(message)

    def set_storage(self, storage_cls: type[SessionStorage] | SessionStorage):
        """set :doc:`session storage <session_storage>`"""
        self.storage = storage_cls(self) if inspect.isclass(storage_cls) else storage_cls
        self.storage.reload()

    def bind_state(self, name: str, dict_ref: dict[str, Any], key: str = "value"):
        """bind component state to :doc:`session storage <session_storage>`

        Arguments:
            name: key name in storage
            dict_ref: binding mapping
            key: key name in binding mapping
        """
        self.storage.add_binding(name, dict_ref, key)

    def bind_states(self, bindings: dict[str, dict | tuple[dict, str]]):
        """bind several components states using short form of dict

        Arguments:
            bindings: dict of dict references or tuples of dict references and keys

        Example::

            session.bind_states({
                "api_token": refs['token'],
                "api_user_id": refs['user_id'],
                "other_value": (refs['other'], "property")
            })
        """
        for k, v in bindings.items():
            if type(v) is tuple:
                self.bind_state(k, *v)
            else:
                self.bind_state(k, v)

    def sync_storage(self):
        """gather changes and save to the :doc:`session storage <session_storage>`"""
        self.storage.gather()
        self.storage.sync()

    def key_events_off(self):
        """send signal to disable all key events"""
        self.send_message(Messages.keys_off())

    def key_events_on(self):
        """send signal to enable all key events"""
        self.send_message(Messages.keys_on())

