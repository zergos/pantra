from __future__ import annotations

from abc import ABC, abstractmethod
import typing
import inspect

from ..oid import get_node
from ..session import trace_errors, trace_errors_async, Session
from ..workers.decorators import thread_worker

if typing.TYPE_CHECKING:
    from typing import *
    from .context import HTMLElement, Context, ReactNode
    from .render.render_node import RenderNode

__all__ = ['DragOptions', 'DragController']


class DragOptions(typing.NamedTuple):
    mouse_button: int = 0
    allow_move_by_x: bool = True
    allow_move_by_y: bool = True
    border_top: Optional[int] = None
    border_left: Optional[int] = None
    border_bottom: Optional[int] = None
    border_right: Optional[int] = None


class DragController(ABC):
    def __init__(self, node: HTMLElement):
        self.from_x: int = 0
        self.from_y: int = 0
        self.x: int = 0
        self.y: int = 0
        self.delta_x: int = 0
        self.delta_y: int = 0

        self.options: DragOptions = self.get_options(node)
        self.in_moving: bool = False

    def get_options(self, node: HTMLElement):
        return DragOptions()

    def mousedown(self, node, x, y, mouse_button):
        if mouse_button != self.options.mouse_button:
            return False
        self.from_x = self.x = x
        self.from_y = self.y = y
        self.in_moving = True
        return self.start(node)

    def mousemove(self, x, y):
        if self.options.allow_move_by_x:
            if self.options.border_left is not None and x < self.options.border_left: x = self.options.border_left
            elif self.options.border_right is not None and x > self.options.border_right: x = self.options.border_right
            self.delta_x = x-self.x
            self.x = x
        if self.options.allow_move_by_y:
            if self.options.border_top is not None and y < self.options.border_top: y = self.options.border_top
            elif self.options.border_bottom is not None and y > self.options.border_bottom: y = self.options.border_bottom
            self.delta_y = y-self.y
            self.y = y
        self.move()

    def mouseup(self):
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
    node: Context = get_node(oid)
    if node is None: return

    func = node[method]
    session.state['drag']: DragController = func(node)
    if session.state['drag'].mousedown(node, x, y, button):
        session.send_message({'m': 'dm'})


@thread_worker
@trace_errors
def process_drag_move(session: Session, x: int, y: int):
    session.state['drag'].mousemove(x, y)


@thread_worker
@trace_errors
def process_drag_stop(session: Session, x: int, y: int):
    session.state['drag'].mouseup()
    del session.state["drag"]

@trace_errors
def process_call(session: Session, node: Context | HTMLElement, method: str, *args):
    for m in method.split(' '):
        if (caller := node.get_caller(m)) is None:
            return
        elif inspect.iscoroutinefunction(caller):
            session.server_worker.run_coroutine(node, caller, trace_errors_async(session, caller(*args)))
        elif callable(caller):
            with session.server_worker.wrap_session_task(node, caller):
                caller(*args)
        else:
            raise ValueError(f"Can`t call type `{type(caller)}` ({caller})")
        #    node[m] = args[0]


@thread_worker
def process_click(session: Session, method: str, oid: int):
    node: HTMLElement = get_node(oid)
    if node is None or not method: return
    process_call(session, node, method, node)


@thread_worker
def process_select(session: Session, method: str, oid: int, opts: List[int]):
    node: HTMLElement = get_node(oid)
    if not node or not method: return
    opts = [get_node(i) for i in opts]
    node._value = len(opts) == 1 and opts[0] or opts
    process_call(session, node, method, node)

@thread_worker
def process_change(session: Session, method: str, oid: int, value: Any):
    node: HTMLElement = get_node(oid)
    if not node: return
    node._value = value
    process_call(session, node, method, node)

def process_bind_value(oid: int, variable: str, value: str):
    node: HTMLElement = get_node(oid)
    if not node: return
    node._value = value
    node.set_quietly(variable, value)

@thread_worker
def process_key(session: Session, method: str, oid: int, key: str):
    node: HTMLElement = get_node(oid)
    if not node or not method: return
    process_call(session, node, method, node, key)


@thread_worker
def process_direct_call(session: Session, oid: int, method: str, args: list[Any]):
    node: Context = get_node(oid)
    if not node or not method: return
    if node.is_call_allowed(method):
        process_call(session, node, method, args)

