from __future__ import annotations

import typing
from typing import TypedDict, TYPE_CHECKING

from .settings import config, logger
from .patching import wipe_logger
from .workers.decorators import thread_worker

if TYPE_CHECKING:
    from .session import Session
    from .components.context import Context
    from .components.render.render_node import RenderNode

@wipe_logger
async def process_message(session: Session, data: dict):
    from .components.controllers import process_drag_start, process_drag_move, process_drag_stop, process_click, \
        process_select, process_key, process_bind_value, process_direct_call, process_change

    command = data['C']
    if command in ('REFRESH', 'UP'):
        if session.just_connected:
            logger.debug("[REFRESH] command (just connected)")
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
                await session.resend_root()
                if session.title:
                    await session.send_title(session.title)
            #await session.recover_messages()
            await session.remind_errors()

    elif command == 'CLICK':
        if not config.WIPE_LOGGING:
            ctx = getattr(session.get_node(data['oid']), 'context', None)
            oid = ctx and ctx.oid or data['oid']
            logger.debug(f"[CLICK] command `{data['method']}` to <{ctx}:{oid}>")
        process_click(session, data['method'], data['oid'])

    elif command == 'SELECT':
        logger.debug(f"[SELECT] command `{data['method']}` to <{getattr(session.get_node(data['oid']), 'context', None)}>")
        process_select(session, data['method'], data['oid'], data['opts'])

    elif command == 'CHANGE':
        logger.debug(f"[CHANGE] command `{data['method']}` to <{getattr(session.get_node(data['oid']), 'context', None)}>")
        process_change(session, data['method'], data['oid'], data['x'])

    elif command == 'KEY':
        logger.debug(f"[KEY] command `{data['method']}` - `{data['key']}` to <{getattr(session.get_node(data['oid']), 'context', None)}>")
        process_key(session, data['method'], data['oid'], data['key'])

    elif command == 'B':
        node = session.get_node(data['oid'])
        logger.debug(f"[B]ound value changed for <{node}:{data['oid']}>")
        if node:
            process_bind_value(node, data['v'], data['x'])

    elif command == 'M':
        node = session.get_node(data['oid'])
        logger.debug(f"[M]easures received for <{node}:{data['oid']}>")
        if node:
            node._set_measures(data['box'])

    elif command == 'V':
        node = session.get_node(data['oid'])
        logger.debug(f"[V]alue received for <{node}:{data['oid']}>")
        if node:
            node._set_value(data['value'])

    elif command == 'DD':
        logger.debug(f"[DD]rag Start `{data['method']}` for <{session.get_node(data['oid'])}:{data['oid']}>")
        process_drag_start(session, data['method'], data['oid'], data['x'], data['y'], data['button'])

    elif command == 'DM':
        logger.debug("[D]rag [M]ove")
        process_drag_move(session, data['x'], data['y'])

    elif command == 'DU':
        logger.debug("[D]rag [S]top")
        process_drag_stop(session, data['x'], data['y'])

    elif command == 'VALID':
        node = session.get_node(data['oid'])
        logger.debug(f"[VALID]ity received for <{node}:{data['oid']}>")
        if node:
            node._set_validity(data['validity'])

    elif command == 'CALL':
        logger.debug(f"[CALL] command `{data['method']}` to  <{getattr(session.get_node(data['oid']), 'context', 'none')}>")
        process_direct_call(session, data['oid'], data['method'], data['args'])


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
    def reconnect():
        return Messages.Command(m="recon")

    @staticmethod
    def error(text: str):
        return Messages.CommandArg(m="e", l=text)

    @staticmethod
    def task_done():
        return Messages.Command(m="0")

    @staticmethod
    def send_context(ctx: Context):
        return Messages.CommandArg(m="c", l=ctx)

    @staticmethod
    def delete(indices: list[int]):
        return Messages.CommandArg(m="d", l=indices)

    @staticmethod
    def update(items: list[RenderNode]):
        return Messages.CommandArg(m="u", l=items)

    @staticmethod
    def request_measures(oid: int):
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
