from dataclasses import dataclass
from typing import *
from anytree import NodeMixin
from attrdict import AttrDict

__all__ = ['UniNode', 'AnyNode', 'DynamicString', 'DynamicClasses']

from core.oid import gen_id


class UniNode(NodeMixin):
    __slots__ = ()

    def __init__(self, parent=None, children=None, *args, **kwargs):
        self.parent = parent
        if children:
            self.children = children

    def append(self, node):
        self._NodeMixin__children_.append(node)

    def clear(self):
        self._NodeMixin__children_.clear()

    def index(self):
        return self._NodeMixin__parent._NodeMixin__children.index(self)

    def __str__(self):
        return self.__class__.__name__

    def __getitem__(self, item):
        return self._NodeMixin__children[item]


class AnyNode(UniNode):
    __slots__ = ['oid', '__weakref__']

    def __init__(self, *args, **kwargs):
        self.oid = gen_id(self)
        super().__init__(*args, **kwargs)


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
    def __add__(self, other):
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
        return DynamicClasses(other)


class DynamicStyles(AttrDict):
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
