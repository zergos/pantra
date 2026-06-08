from __future__ import annotations

from abc import ABC, abstractmethod
import typing
import inspect

from .render.render_node import RenderNode
from ..session import trace_errors, trace_errors_async, Session
from ..workers.decorators import thread_worker

if typing.TYPE_CHECKING:
    from typing import *
    from .context import HTMLElement, Context

__all__ = ['DragOptions', 'DragController']


class DragOptions(typing.NamedTuple):
    """Initial drag'n'drop control options

    Attributes:
        mouse_button: code of `mouse button <https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/button>`__ to push for drag
        allow_move_by_x: allow move dragged box by x-axis
        allow_move_by_y: allow move dragged box by y-axis
        border_top: drag zone border top max coordinate
        border_bottom: border bottom max coordinate
        border_left: border left max coordinate
        border_right: border right max coordinate
    """
    mouse_button: int = 0
    allow_move_by_x: bool = True
    allow_move_by_y: bool = True
    border_top: Optional[int] = None
    border_left: Optional[int] = None
    border_bottom: Optional[int] = None
    border_right: Optional[int] = None


class DragController(ABC):
    """Abstract class to perform drag'n'drop action

    Attributes:
        from_x: initial x coordinate
        from_y: initial y coordinate
        x: current x coordinate
        y: current y coordinate
        delta_x: changes of x coordinate since last time
        delta_y: changes of y coordinate since last time
        options: control options
        in_moving: box in moving process
    """
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
        """get options for node

        Override this method for custom options for specified node
        """
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
        """method invoked when drag action performed and satisfied to options"""
        return False

    @abstractmethod
    def move(self):
        """method invoked on drag box moving"""

    @abstractmethod
    def stop(self):
        """method invoked on drag box drop"""


@thread_worker
@trace_errors
def process_drag_start(session: Session, method: str, oid: int, x: int, y: int, button: int):
    node: Context = session.get_node(oid)
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
        if m.startswith('update:'):
            ref_name = m[len('update:'):]
            ref_node = node.context.refs.get(ref_name)
            if ref_node is None:
                raise ValueError(f"No such ref: `{ref_name}`")
            if not isinstance(ref_node, RenderNode):
                raise ValueError(f"Ref: `{ref_name}` must be a RenderNode")
            ref_node.update(True)
            return

        if m.startswith('scope:'):
            scope_name = m[len('scope:'):]
            try:
                caller = node.context.scope[scope_name]
            except KeyError:
                raise ValueError(f"No such scope data: `{scope_name}`")
        else:
            caller = node.get_caller(m)

        if caller is None:
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
    node: HTMLElement = session.get_node(oid)
    if node is None or not method: return
    process_call(session, node, method, node)


@thread_worker
def process_select(session: Session, method: str, oid: int, opts: List[int]):
    node: HTMLElement = session.get_node(oid)
    if not node or not method: return
    opts = [session.get_node(i) for i in opts]
    node._value = len(opts) == 1 and opts[0] or opts
    process_call(session, node, method, node)

@thread_worker
def process_change(session: Session, method: str, oid: int, value: Any):
    node: HTMLElement = session.get_node(oid)
    if not node: return
    node._value = value
    process_call(session, node, method, node)

def process_bind_value(node: HTMLElement, variable: str, value: str):
    node._value = value
    node.set_quietly(variable, value)

@thread_worker
def process_key(session: Session, method: str, oid: int, key: str):
    node: HTMLElement = session.get_node(oid)
    if not node or not method: return
    process_call(session, node, method, node, key)


@thread_worker
def process_direct_call(session: Session, oid: int, method: str, args: list[Any]):
    node: Context = session.get_node(oid)
    if not node or not method: return
    if node.is_call_allowed(method):
        process_call(session, node, method, args)

