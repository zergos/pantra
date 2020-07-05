from __future__ import annotations

import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['typename', 'ADict', 'UniNode', 'UniqueNode', 'DynamicString', 'DynamicClasses', 'DynamicStyles', 'WebUnits', 'patch_typing']

from .oid import gen_id


def typename(t):
    return type(t).__name__


TADict = typing.TypeVar('TADict', bound='ADict')


class ADict(dict):
    __setattr__ = dict.__setitem__  
    __delattr__ = dict.__delitem__  

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError

    def __or__(self: TADict, other: Dict) -> TADict:
        res = self.__class__(self)
        res.update(other)
        return res

    def __sub__(self: TADict, other: Iterable) -> TADict:
        res = self.__class__(self)
        for k in other:
            if k in res:
                del res[k]
        return res

    def __truediv__(self: TADict, other: Iterable) -> Tuple[TADict, TADict]:
        res = self.__class__(self)
        res2 = self.__class__()
        for k in other:
            if k in res:
                res2[k] = res[k]
                del res[k]
        return res, res2


TUniNode = typing.TypeVar('TUniNode', bound='UniNode')


class UniNode:
    __slots__ = ['_children', '_parent']

    def __init__(self, parent: Optional[UniNode] = None):
        self._parent: Optional[UniNode] = parent
        if parent:
            parent.append(self)
        self._children: List[UniNode] = []

    @property
    def parent(self: TUniNode) -> TUniNode:
        return self._parent  

    @parent.setter
    def parent(self: TUniNode, parent: Optional[TUniNode]):
        if self._parent:
            self._parent._children.remove(self)
        if parent:
            parent.append(self)
        self._parent = parent

    @property
    def children(self: TUniNode) -> List[TUniNode]:
        return self._children  

    def append(self: TUniNode, node: TUniNode):
        self._children.append(node)

    def remove(self: TUniNode, node: TUniNode):
        node.parent = None

    def clear(self):
        self._children.clear()

    def index(self):
        return self._parent._children.index(self)

    def move(self, from_i: int, to_i: int):
        if from_i == to_i:
            return
        self._children.insert(to_i, self._children.pop(from_i))

    def __contains__(self, item):
        return item in self._children

    def __getitem__(self: TUniNode, item) -> TUniNode:
        return self._children[item]

    def __iter__(self: TUniNode) -> Iterable[TUniNode]:
        yield from self._children  

    def path(self) -> str:
        if not self._parent:
            return str(self)
        return f'{self._parent.path()}/{self}'

    def select(self: TUniNode, predicate: Callable[[TUniNode], bool]) -> Iterable[TUniNode]:
        for child in self._children:
            if predicate(child):  
                yield child  
            yield from child.select(predicate)  

    def upto(self: TUniNode, predicate: Union[str, Callable[[TUniNode], bool]]) -> Optional[TUniNode]:
        node = self._parent
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


def patch_typing(f):
    pass
