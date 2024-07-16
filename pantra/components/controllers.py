from __future__ import annotations

from abc import ABC, abstractmethod
import typing
import asyncio
import inspect

from ..oid import get_node
from ..session import trace_errors, trace_errors_async, Session
from ..workers.decorators import thread_worker

if typing.TYPE_CHECKING:
    from typing import *
    from ..components.context import Context, RenderNode, HTMLElement, AnyNode

__all__ = ['DragOptions', 'DragController']


class DragOptions(typing.NamedTuple):
    button: int = 0
    allow_x: bool = True
    allow_y: bool = True
    top: Optional[int] = None
    left: Optional[int] = None
    bottom: Optional[int] = None
    right: Optional[int] = None


class DragController(ABC):
    def __init__(self, node: HTMLElement):
        self.from_x: int = 0
        self.from_y: int = 0
        self.x: int = 0
        self.y: int = 0
        self.delta_x: int = 0
        self.delta_y: int = 0

        self.mode: DragOptions = self.get_options(node)
        self.in_moving: bool = False

    def get_options(self, node: HTMLElement):
        return DragOptions()

    def _mousedown(self, node, x, y, button):
        if button != self.mode.button:
            return False
        self.from_x = self.x = x
        self.from_y = self.y = y
        self.in_moving = True
        return self.start(node)

    def _mousemove(self, x, y):
        if self.mode.allow_x:
            if self.mode.left is not None and x < self.mode.left: x = self.mode.left
            elif self.mode.right is not None and x > self.mode.right: x = self.mode.right
            self.delta_x = x-self.x
            self.x = x
        if self.mode.allow_y:
            if self.mode.top is not None and y < self.mode.top: y = self.mode.top
            elif self.mode.bottom is not None and y > self.mode.bottom: y = self.mode.bottom
            self.delta_y = y-self.y
            self.y = y
        self.move()

    def _mouseup(self):
        self.in_moving = False
        self.stop()

    @abstractmethod
    def start(self, node) -> bool:
        return False

    @abstractmethod
    def move(self):
        pass

    @abstractmethod
    def stop(self):
        pass


@thread_worker
@trace_errors
def process_drag_start(session: Session, method: str, oid: int, x: int, y: int, button: int):
    node: AnyNode = get_node(oid)
    if node is None: return

    func = node[method]
    session.state.drag: DragController = func(node)
    if session.state.drag._mousedown(node, x, y, button):
        session.send_message({'m': 'dm'})


@thread_worker
@trace_errors
def process_drag_move(session: Session, x: int, y: int):
    session.state.drag._mousemove(x, y)


@thread_worker
@trace_errors
def process_drag_stop(session: Session, x: int, y: int):
    session.state.drag._mouseup()
    delattr(session.state, "drag")


@trace_errors
def process_call(node: AnyNode, method: str, *args):
    session = node.context.session
    for m in method.split(' '):
        if inspect.iscoroutinefunction(caller:=node[m]):
            session.server_worker.run_coroutine(node, caller, trace_errors_async(session, caller(*args)))
        elif callable(caller):
            with session.server_worker.wrap_session_task(node, caller):
                caller(*args)
        elif caller is not None:
            raise ValueError(f"Can`t call type `{type(caller)}` ({caller})")
        #    node[m] = args[0]


@thread_worker
def process_click(method: str, oid: int):
    node = get_node(oid)
    if node is None or not method: return
    process_call(node, method, node)


@thread_worker
def process_select(method: str, oid: int, opts: List[int]):
    node = get_node(oid)
    if not node or not method: return
    opts = [get_node(i) for i in opts]
    node._value = len(opts) == 1 and opts[0] or opts
    process_call(node, method, node)


@thread_worker
def process_bind_value(oid: int, method: str, value: str):
    node: HTMLElement = get_node(oid)
    if not node: return
    node.value = value
    if method != 'value':
        process_call(node, method, node)
    else:
        node.set_quietly('value', value)

@thread_worker
def process_key(method: str, oid: int, key: str):
    node = get_node(oid)
    if not node or not method: return
    process_call(node, method, node, key)


@thread_worker
def process_direct_call(oid: int, method: str, args: list[Any]):
    node = get_node(oid)
    if not node or not method: return
    if node.is_call_allowed(method):
        process_call(node, method, args)

