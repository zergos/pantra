import ctypes
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NamedTuple, Optional

from core.components.context import Context, AnyNode
from core.oid import get_object
from core.session import Session
from core.workers import thread_worker


class Controller(ABC):
    pass


class DragOptions(NamedTuple):
    button: int = 1
    allow_x: bool = True
    allow_y: bool = True
    top: Optional[int] = None
    left: Optional[int] = None
    bottom: Optional[int] = None
    right: Optional[int] = None


@dataclass
class DragController(Controller):
    from_x: int = 0
    from_y: int = 0
    x: int = 0
    y: int = 0
    delta_x: int = 0
    delta_y: int = 0

    mode: DragOptions = None
    in_moving: bool = False

    def __post_init__(self):
        self.mode = self.get_options()

    def get_options(self):
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
    def start(self, node):
        return False

    @abstractmethod
    def move(self):
        pass

    @abstractmethod
    def stop(self):
        pass


def process_drag_start(method: str, oid: int, x: int, y: int, button: int):
    node: AnyNode = get_object(oid)
    node.session.state.drag: DragController = node.context.locals[method]()
    return node.session.state.drag._mousedown(node, x, y, button)


def process_drag_move(session: Session, x: int, y: int):
    session.state.drag._mousemove(x, y)


def process_drag_stop(session: Session, x: int, y: int):
    session.state.drag._mouseup(x, y)
    delattr(session.state, "drag")


@thread_worker
def process_click(method: str, oid: int):
    node = get_object(oid)
    context = node.context
    process_click_referred(method, context, node)


def process_click_referred(method: str, context: Context, node: AnyNode):
    if method in context.locals:
        if callable(context.locals[method]):
            try:
                context.locals[method](node)
            except:
                node.session.send_error(traceback.format_exc())
        else:
            process_click_referred(context.locals[method], context.parent.context, node)
