from collections import namedtuple
from dataclasses import dataclass


class Controller:
    pass


DragOptions = namedtuple('DragMode', ['mouse_button', 'allow_x', 'allow_y', 'top', 'left', 'bottom', 'right'])


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
        return DragOptions(1, True, True, None, None, None, None)

    def _mousedown(self, node, x, y, mouse_button):
        if mouse_button != self.mode.mouse_button:
            return
        self.from_x = self.x = x
        self.from_y = self.y = y
        self.in_moving = True
        self.start(node)

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

    def start(self, node):
        pass

    def move(self):
        pass

    def stop(self):
        pass
