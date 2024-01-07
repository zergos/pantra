from __future__ import annotations

import types
import typing
import ctypes

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['typename', 'ADict', 'UniNode', 'UniqueNode', 'DynamicString', 'DynamicClasses', 'DynamicStyles', 'WebUnits',
           'EmptyCaller', 'define_getter', 'define_setter', 'DynamicValue', 'raise_exception_in_thread']

from .oid import gen_id


def typename(t):
    return type(t).__name__


T1 = typing.TypeVar('T1')
T2 = typing.TypeVar('T2')


class ADict(dict, typing.Generic[T1, T2]):
    __setattr__ = dict.__setitem__  
    __delattr__ = dict.__delitem__  

    def __getattr__(self, item: T1) -> T2:
        try:
            return self[item]
        except KeyError:
            raise AttributeError

    def __or__(self, other: ADict) -> Self:
        res = self.__class__(self)
        res.update(other)
        return res

    def __sub__(self, other: Iterable) -> Self:
        res = self.__class__(self)
        for k in other:
            if k in res:
                del res[k]
        return res

    def __truediv__(self, other: Iterable) -> Tuple[Self, Self]:
        res = self.__class__(self)
        res2 = self.__class__()
        for k in other:
            if k in res:
                res2[k] = res[k]
                del res[k]
        return res, res2


class UniNode:
    __slots__ = ['_children', '_parent']

    def __init__(self, parent: Optional[UniNode] = None):
        self._parent: UniNode | None = parent
        if parent:
            parent.append(self)
        self._children: list[UniNode] = []

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

    def append(self, node: UniNode):
        self._children.append(node)

    def remove(self, node: UniNode):
        node.parent = None

    def clear(self):
        self._children.clear()

    def index(self):
        return self._parent._children.index(self)

    def move(self, from_i: int, to_i: int):
        if from_i == to_i:
            return
        self._children.insert(to_i, self._children.pop(from_i))

    def __contains__(self, item: UniNode):
        return item in self._children

    def __getitem__(self, item: int) -> Self:
        return self._children[item]

    def __iter__(self) -> Iterable[Self]:
        yield from self._children  

    def path(self) -> str:
        if not self._parent:
            return str(self)
        return f'{self._parent.path()}/{self}'

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
        value = func() if isinstance(func, types.FunctionType) else func
        instance = super().__new__(cls, value)
        if isinstance(value, DynamicString):
            instance.html = value.html
        return instance

    def __init__(self, func: Callable[[], str] | str):
        self.func: Callable[[], str] = func
        if not hasattr(self, "html"):
            self.html = False

    def __call__(self, *args, **kwargs) -> Self:
        return self.__class__(self.func)

    def __add__(self, other):
        if not other:
            return self.__class__(self.func)
        return self+other

    def __getstate__(self):
        return str(self)

    def __setstate__(self, state):
        self.func = lambda: state


class DynamicHTML(DynamicString):
    def __init__(self, func: Callable[[], str] | str):
        super().__init__(func)
        self.html = True


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


class DynamicStyles(ADict):
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
        return ';'.join(f'{k.replace("_","-")}: {v}' for k, v in self.items() if v not in ('', None))

    def __enter__(self):
        return self.copy()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __sub__(self, other):
        if other in self:
            del self[other]
        return self


class WebUnits(str):
    __slots__ = ['value', 'unit']

    def __new__(cls, value: int | float | str, unit: str = 'px'):
        if type(value) != str:
            return super().__new__(cls, f'{value}{unit}')
        else:
            return super().__new__(cls, value)

    def __init__(self, value: int | float | str, unit: str = 'px'):
        if type(value) != str:
            self.value = value
            self.unit = unit
        else:
            pos = next((i for i, c in enumerate(value) if not c.isdigit()), len(value))
            self.value = int(value[:pos])
            self.unit = value[pos:]

    def __add__(self, other: int | float):
        return WebUnits(self.value + other, self.unit)

    def __sub__(self, other: int | float):
        return WebUnits(self.value - other, self.unit)

    def __mul__(self, other):
        return WebUnits(self.value * other, self.unit)

    def __truediv__(self, other):
        return WebUnits(self.value / other, self.unit)

    def __floordiv__(self, other):
        return WebUnits(self.value // other, self.unit)

    def __neg__(self):
        return WebUnits(-self.value, self.unit)


class EmptyCaller(str):
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
