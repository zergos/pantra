from collections import namedtuple
from dataclasses import dataclass

DragOptions = namedtuple('DragMode', ['button', 'allow_x', 'allow_y', 'top', 'left', 'bottom', 'right'])


@dataclass
class DragController:
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
        return DragOptions(1, True, True, 0, 0, 0, 0)

    def _mousedown(self, node, x, y, button):
        if button != self.mode.button:
            return
        self.from_x = self.x = x
        self.from_y = self.y = y
        self.in_moving = True
        self.start(node)

    def _mousemove(self, x, y):
        if self.mode.allow_x:
            self.delta_x = x-self.x
            self.x = x
        if self.mode.allow_y:
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
