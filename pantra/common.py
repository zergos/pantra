from __future__ import annotations

import typing
import ctypes

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['typename', 'UniNode', 'UniqueNode', 'DynamicString', 'DynamicClasses', 'DynamicStyles', 'WebUnits',
           'EmptyCaller', 'define_getter', 'define_setter', 'DynamicValue', 'raise_exception_in_thread',
           'DynamicHTML']

from .oid import gen_id


def typename(t):
    return type(t).__name__

ValueT = typing.TypeVar('ValueT')

class UniNode:
    __slots__ = ['_children', '_parent']

    def __init__(self, parent: Optional[Self] = None):
        self._parent: Self | None = parent
        if parent:
            parent.append(self)
        self._children: list[Self] = []

    @property
    def parent(self) -> Self:
        return self._parent  

    @parent.setter
    def parent(self, parent: Self | None):
        if self._parent:
            self._parent._children.remove(self)
        if parent:
            parent.append(self)
        self._parent = parent

    @property
    def children(self) -> list[Self]:
        return self._children  

    def append(self, node: Self):
        self._children.append(node)

    def remove(self, node: Self):
        node.parent = None

    def clear(self):
        self._children.clear()

    def index(self):
        return self._parent._children.index(self)

    def move_child(self, from_i: int, to_i: int):
        if from_i == to_i:
            return
        self._children.insert(to_i, self._children.pop(from_i))

    def move(self, to_i: int):
        if not self._parent:
            return
        self._parent.move_child(self.index(), to_i)

    def __contains__(self, item: Self):
        return item in self._children

    def __getitem__(self, item: int) -> Self:
        return self._children[item]

    def __iter__(self) -> Iterable[Self]:
        yield from self._children  

    def path(self) -> str:
        if not self._parent:
            return str(self)
        return f'{self._parent.path()}/{self}'

    @property
    def root(self):
        res = self
        while res.parent:
            res = res.parent
        return res

    def select(self, predicate: Callable[[Self], bool], depth: int = None) -> Generator[Self]:
        for child in self._children:
            if predicate(child):  
                yield child
            if depth is None:
                yield from child.select(predicate)
            elif depth > 1:
                yield from child.select(predicate, depth-1)

    def upto(self, predicate: Union[str, Callable[[Self], bool]]) -> Optional[Self]:
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

    def downto(self, predicate: Callable[[Self], bool], depth: int = None) -> Optional[Self]:
        return next(self.select(predicate, depth), None)


class UniqueNode(UniNode):
    __slots__ = ['oid', '__weakref__']

    def __init__(self, parent=None):
        self.oid = gen_id(self)
        super().__init__(parent)

class DynamicString(str):
    __slots__ = ['func', 'html']

    def __new__(cls, func: Callable[[], str] | str):
        value = func() if callable(func) else func
        if isinstance(value, DynamicString):
            return value
        instance = super().__new__(cls, value)
        instance.func = func
        instance.html = False
        return instance

    def update(self) -> Self:
        return self.__class__(self.func)

class DynamicHTML(DynamicString):
    def __new__(cls, func):
        instance = super().__new__(cls, func)
        instance.html = True
        return instance

class DynamicValue:
    __slots__ = ['func', 'value']

    def __init__(self, func: Callable[[], Any]):
        self.func: Callable[[], Any] = func
        self.value = func()

    def update(self):
        self.value = self.func()
        return self.value

    def __getstate__(self):
        return self.value

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


class DynamicStyles(dict[str, typing.Union[str, int, 'WebUnits']]):
    __slots__ = []
    def __init__(self, style: dict | str | None = None):
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
        return ';'.join(f'{k}: {v}' for k, v in self.items())


class WebUnits(str):
    __slots__ = ['value', 'unit']

    def __new__(cls, value: int | float | str, unit: str = 'px'):
        if not isinstance(value, str):
            return super().__new__(cls, f'{value}{unit}')
        else:
            return super().__new__(cls, value)

    def __init__(self, value: int | float | str, unit: str = 'px'):
        if not isinstance(value, str):
            self.value = value
            self.unit = unit
        elif not value:
            raise ValueError('value cannot be empty')
        else:
            pos = next((i for i, c in enumerate(value) if not c.isdigit()), len(value))
            self.value = int(value[:pos])
            self.unit = value[pos:]

    def __add__(self, other: int | float):
        if not other: return self
        return WebUnits(self.value + other, self.unit)

    def __sub__(self, other: int | float):
        if not other: return self
        return WebUnits(self.value - other, self.unit)

    def __mul__(self, other):
        if other == 1: return self
        return WebUnits(self.value * other, self.unit)

    def __truediv__(self, other):
        if other == 1: return self
        return WebUnits(self.value / other, self.unit)

    def __floordiv__(self, other):
        if other == 1: return self
        return WebUnits(self.value // other, self.unit)

    def __neg__(self):
        return WebUnits(-self.value, self.unit)


class EmptyCaller(str):
    __name__ = 'EmptyCaller'

    def __new__(cls):
        return super().__new__(cls, '')

    def __call__(self, *args, **kwargs):
        pass


def define_getter(src, name='getter', locals = None):
    locals = locals or {}
    exec(f'def {name}(self): return {src}', locals)
    return locals[name]


def define_setter(src, name='setter', locals = None):
    locals = locals or {}
    exec(f'def {name}(self, value): {src}', locals)
    return locals[name]


def raise_exception_in_thread(thread_id):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print('Exception raise failure')
