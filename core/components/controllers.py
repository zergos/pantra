from __future__ import annotations

from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, TYPE_CHECKING, List

from core.oid import get_node
from core.session import trace_errors, Session
from core.workers import thread_worker

if TYPE_CHECKING:
    from core.components.context import Context, RenderNode, HTMLElement, AnyNode

__all__ = ['DragOptions', 'DragController']


class DragOptions(NamedTuple):
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
def process_drag_start(session: Session, method: str, oid: int, x: int, y: int, button: int):
    node: AnyNode = get_node(oid)
    if node is None: return
    process_drag_referred(session, node, method, x, y, button)


@trace_errors
def process_drag_referred(session: Session, node: AnyNode, method: str, x: int, y: int, button: int):
    func = node[method]
    if type(func) == str:
        process_click_referred.call(session, node.context.parent, method, x, y, button)
    else:
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


@thread_worker
def process_click(method: str, oid: int):
    node = get_node(oid)
    if node is None or not method: return
    context = node.context
    process_click_referred(context.session, context, method, node)


@trace_errors
def process_click_referred(session: Session, context: Context, method: str, node: RenderNode):
    if ' ' in method:
        for m in method.split(' '):
            process_click_referred.call(session, context, m, node)
    func = context[method]
    if not func: return
    if callable(func):
        func(node)
    elif context.parent:
        process_click_referred.call(session, context.parent.context, func, node)


@thread_worker
def process_select(method: str, oid: int, opts: List[int]):
    node = get_node(oid)
    if not node or not method: return
    opts = [get_node(i) for i in opts]
    node._value = len(opts) == 1 and opts[0] or opts
    process_click_referred(node.context.session, node.context, method, node)


@thread_worker
def process_bind_value(oid: int, var_name: str, value: str):
    node = get_node(oid)
    if not node: return
    node.context.locals[var_name] = value
    node.attributes.value = value
