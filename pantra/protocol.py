from __future__ import annotations

import logging
import typing
from typing import TypedDict, TYPE_CHECKING

from .oid import get_node
from .settings import config
from .patching import wipe_logger
from .workers.decorators import thread_worker

if TYPE_CHECKING:
    from .session import Session
    from .components.context import Context, AnyNode

logger = logging.getLogger('pantra.system')

@wipe_logger
async def process_message(session: Session, data: dict):
    from .components.context import HTMLElement
    from .components.controllers import process_drag_start, process_drag_move, process_drag_stop, process_click, \
        process_select, process_key, process_bind_value, process_direct_call

    command = data['C']
    if command in ('REFRESH', 'UP'):
        if session.just_connected:
            session.just_connected = False

            @thread_worker
            def restart():
                session.restart()

            restart()
        else:
            if command == 'REFRESH':
                logger.debug("[REFRESH] command")
                if hasattr(session.state, 'drag'):
                    process_drag_stop(session, 0, 0)
                await session.send_root()
                if session.title:
                    await session.send_title(session.title)
            #await session.recover_messages()
            await session.remind_errors()

    elif command == 'CLICK':
        if config.ENABLE_LOGGING:
            ctx = getattr(get_node(data['oid']), 'context', None)
            oid = ctx and ctx.oid or data['oid']
            logger.debug(f"[CLICK] command `{data['method']}` to <{ctx}:{oid}>")
        process_click(data['method'], data['oid'])

    elif command == 'SELECT':
        logger.debug(f"[SELECT] command `{data['method']}` to <{getattr(get_node(data['oid']), 'context', None)}>")
        process_select(data['method'], data['oid'], data['opts'])

    elif command == 'KEY':
        logger.debug(f"[KEY] command `{data['method']}` - `{data['key']}` to <{getattr(get_node(data['oid']), 'context', None)}>")
        process_key(data['method'], data['oid'], data['key'])

    elif command == 'B':
        logger.debug("[B]ind value command")
        process_bind_value(data['oid'], data['v'], data['x'])

    elif command == 'M':
        logger.debug(f"[M]etrics received for <{get_node(data['oid'])}:{data['oid']}>")
        HTMLElement._set_metrics(data['oid'], data)

    elif command == 'V':
        logger.debug(f"[V]alue received for <{get_node(data['oid'])}:{data['oid']}>")
        HTMLElement._set_value(data['oid'], data['value'])

    elif command == 'DD':
        logger.debug(f"[DD]rag Start `{data['method']}` for <{get_node(data['oid'])}:{data['oid']}>")
        process_drag_start(session, data['method'], data['oid'], data['x'], data['y'], data['button'])

    elif command == 'DM':
        logger.debug("[D]rag [M]ove")
        process_drag_move(session, data['x'], data['y'])

    elif command == 'DU':
        logger.debug("[D]rag [S]top")
        process_drag_stop(session, data['x'], data['y'])

    elif command == 'VALID':
        logger.debug(f"[VALID]ity received for <{get_node(data['oid'])}:{data['oid']}>")
        HTMLElement._set_validity(data['oid'], data['validity'])

    elif command == 'CALL':
        logger.debug(f"[CALL] command `{data['method']}` to  <{getattr(get_node(data['oid']), 'context', 'none')}>")
        process_direct_call(data['oid'], data['method'], data['args'])


class Messages:
    class Command(TypedDict):
        m: str

    class CommandArg(Command):
        l: typing.Any

    class RequestValue(CommandArg):
        t: str

    class Call(Command):
        method: str
        args: typing.Sequence[typing.Any]

    @staticmethod
    def restart():
        return Messages.Command(m="rst")

    @staticmethod
    def error(text: str):
        return Messages.CommandArg(m="e", l=text)

    @staticmethod
    def send_context(ctx: Context):
        return Messages.CommandArg(m="c", l=ctx)

    @staticmethod
    def delete(indices: list[int]):
        return Messages.CommandArg(m="d", l=indices)

    @staticmethod
    def update(items: list[AnyNode]):
        return Messages.CommandArg(m="u", l=items)

    @staticmethod
    def request_metrics(oid: int):
        return Messages.CommandArg(m="m", l=oid)

    @staticmethod
    def request_value(oid: int, typ: str):
        return Messages.RequestValue(m="v", l=oid, t=typ)

    @staticmethod
    def request_validity(oid: int):
        return Messages.CommandArg(m="valid", l=oid)

    @staticmethod
    def log(message: str):
        return Messages.CommandArg(m="log", l=message)

    @staticmethod
    def call(method: str, args: typing.Sequence[typing.Any]):
        return Messages.Call(m="call", method=method, args=args)

    @staticmethod
    def start_app(app: str):
        return Messages.CommandArg(m="app", l=app)

    @staticmethod
    def set_title(title: str):
        return Messages.CommandArg(m="title", l=title)

    @staticmethod
    def keys_off():
        return Messages.Command(m="koff")

    @staticmethod
    def keys_on():
        return Messages.Command(m="kon")

