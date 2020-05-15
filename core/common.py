from contextlib import contextmanager
from dataclasses import dataclass
from typing import *

__all__ = ['ADict', 'UniNode', 'UniqueNode', 'DynamicString', 'DynamicClasses']

from core.oid import gen_id


def typename(t):
    return type(t).__name__


class ADict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__
    __delattr__ = dict.__delitem__


class UniNode:
    __slots__ = ['children', '_parent']

    def __init__(self, parent: Optional['UniNode'] = None):
        self._parent: Optional[UniNode] = parent
        if parent:
            parent.append(self)
        self.children: List[UniNode] = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if self._parent:
            self._parent.remove(self)
        if parent:
            parent.append(self)
        self._parent = parent

    def append(self, node):
        self.children.append(node)

    def remove(self, node):
        self.children.remove(node)

    def clear(self):
        self.children.clear()

    def index(self):
        return self._parent.children.index(self)

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        return self.children[item]


class UniqueNode(UniNode):
    __slots__ = ['oid', '__weakref__']

    def __init__(self, parent=None):
        self.oid = gen_id(self)
        super().__init__(parent)


class DynamicString(str):
    __slots__ = ['func']

    def __new__(cls, func: Callable[[], str]):
        return super().__new__(cls, func() if callable(func) else func)

    def __init__(self, func: Callable[[], str]):
        self.func: Callable[[], str] = func

    def __call__(self, *args, **kwargs) -> 'DynamicString':
        return DynamicString(self.func)

    def __add__(self, other):
        if not other:
            return DynamicString(self.func)
        return self+other

    def __getstate__(self):
        return str(self)

    def __setstate__(self, state):
        self.func = lambda: state


class DynamicClasses(str):
    __slots__ = []

    def __add__(self, other):
        if not other: return self
        return DynamicClasses(super().__add__(f' {other}'))

    def __sub__(self, other):
        if self == other:
            return DynamicClasses('')
        l = self.split(' ')
        if other not in l:
            return self
        l.remove(other)
        return DynamicClasses(' '.join(l))

    def __mul__(self, other):
        if other in self:
            return self - other
        else:
            return self + other


class DynamicStyles(ADict):
    def __init__(self, style: Optional[str] = None):
        if style:
            data = {
                expr.split('=')[0].strip(): expr.split('=')[1].strip()
                for expr in style.split(';') if expr.strip()
            }
            super().__init__(data)
        else:
            super().__init__()

    def __str__(self):
        return ';'.join(f'{k.replace("_","-")}: {v}' for k, v in self.items())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __sub__(self, other):
        if other in self:
            del self[other]
        return self


@dataclass
class MetricsData:
    __slots__ = ['left', 'top', 'right', 'bottom', 'width', 'height']
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int


class WebUnits(str):
    __slots__ = ['value', 'unit']

    def __new__(cls, value: Union[int, float, str], unit: str = 'px'):
        if type(value) != str:
            return super().__new__(cls, f'{value}{unit}')
        else:
            return super().__new__(cls, value)

    def __init__(self, value: Union[int, float, str], unit: str = 'px'):
        if type(value) != str:
            self.value = value
            self.unit = unit
        else:
            pos = next((i for i, c in enumerate(value) if not c.isdigit()), len(value))
            self.value = int(value[:pos])
            self.unit = value[pos:]

    def __add__(self, other: Union[int, float]):
        return WebUnits(self.value + other, self.unit)

    def __sub__(self, other: Union[int, float]):
        return WebUnits(self.value - other, self.unit)


class EmptyCaller(str):
    def __new__(cls):
        return super().__new__(cls, '')

    def __call__(self, *args, **kwargs):
        return None
