from __future__ import annotations

import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['typename', 'ADict', 'UniNode', 'UniqueNode', 'DynamicString', 'DynamicClasses', 'DynamicStyles', 'WebUnits']

from .oid import gen_id


def typename(t):
    return type(t).__name__


class ADict(dict):
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError

    def __or__(self, other: Dict):
        res = self.__class__(self)
        res.update(other)
        return res

    def __sub__(self, other: Iterable):
        res = self.__class__(self)
        for k in other:
            if k in res:
                del res[k]
        return res

    def __truediv__(self, other: Iterable):
        res = self.__class__(self)
        res2 = self.__class__()
        for k in other:
            if k in res:
                res2[k] = res[k]
                del res[k]
        return res, res2


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
            self._parent.children.remove(self)
        if parent:
            parent.append(self)
        self._parent = parent

    def append(self, node):
        self.children.append(node)

    def remove(self, node):
        node.parent = None

    def clear(self):
        self.children.clear()

    def index(self):
        return self._parent.children.index(self)

    def move(self, from_i: int, to_i: int):
        if from_i == to_i:
            return
        self.children.insert(to_i, self.children.pop(from_i))

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        return self.children[item]

    def __iter__(self):
        yield from self.children

    def path(self):
        if not self.parent:
            return str(self)
        return f'{self.parent.path()}/{self}'

    def select(self, predicate: Callable[['UniNode'], bool]) -> Generator['UniNode']:
        for child in self.children:
            if predicate(child):
                yield child
            yield from child.select(predicate)

    def upto(self, predicate: Union[str, Callable[['UniNode'], bool]]) -> Optional['UniNode']:
        node = self.parent
        while node:
            if isinstance(predicate, str):
                if str(node) == predicate:
                    return node
            else:
                if predicate(node):
                    return node
            node = node.parent
        return None


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
        if not self: return DynamicClasses(other)
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
    def __init__(self, style: Optional[Union[dict, str]] = None):
        if style:
            if isinstance(style, dict):
                super().__init__(style)
            else:
                data = {
                    expr.split(':')[0].strip(): expr.split(':')[1].strip()
                    for expr in style.split(';') if expr.strip()
                }
                super().__init__(data)
        else:
            super().__init__()

    def __str__(self):
        return ';'.join(f'{k.replace("_","-")}: {v}' for k, v in self.items() if v not in ('', None))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __sub__(self, other):
        if other in self:
            del self[other]
        return self


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

    def __mul__(self, other):
        return WebUnits(self.value * other, self.unit)

    def __truediv__(self, other):
        return WebUnits(self.value / other, self.unit)

    def __floordiv__(self, other):
        return WebUnits(self.value // other, self.unit)


class EmptyCaller(str):
    def __new__(cls):
        return super().__new__(cls, '')

    def __call__(self, *args, **kwargs):
        return None
