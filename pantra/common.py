from __future__ import annotations

import types
import typing
import ctypes
import itertools

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['typename', 'UniNode', 'UniqueNode', 'DynamicClasses', 'DynamicStyles', 'WebUnits',
           'EmptyCaller', 'raise_exception_in_thread', 'HTML', 'DynamicDict', 'ScopeDict']

from .oid import OIDGenerator


def typename(t):
    return type(t).__name__

class UniNode:
    """Simple tree of nodes"""
    __slots__ = ['_children', '_parent']

    def __init__(self, parent: Optional[Self] = None):
        self._parent: Self | None = parent
        if parent:
            parent.append(self)
        self._children: list[Self] = []

    @property
    def parent(self) -> Self:
        """parent property"""
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
        """children property"""
        return self._children  

    def append(self, node: Self):
        """append node to children"""
        self._children.append(node)

    def remove(self, node: Self):
        """remove node from children"""
        node.parent = None

    def clear(self):
        """clear all children"""
        self._children.clear()

    def index(self):
        """return index of current node"""
        return self._parent._children.index(self)

    def move_child(self, from_i: int, to_i: int):
        """move child node from one index to another"""
        if from_i == to_i:
            return
        self._children.insert(to_i, self._children.pop(from_i))

    def move(self, to_i: int):
        """move this node to another index"""
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
        """return path of current node"""
        if not self._parent:
            return str(self)
        return f'{self._parent.path()}/{self}'

    @property
    def root(self):
        """return root node of this tree"""
        res = self
        while res.parent:
            res = res.parent
        return res

    def select(self, predicate: Callable[[Self], bool], depth: int = None) -> Generator[Self]:
        """select all nodes by predicate condition

        Arguments:
            predicate: lambda expression, checking each item for condition
            depth: amount of levels depth for recursion

        Yields:
            selected node
        """
        for child in self._children:
            if predicate(child):  
                yield child
            if depth is None:
                yield from child.select(predicate)
            elif depth > 1:
                yield from child.select(predicate, depth-1)

    def upto(self, predicate: Union[str, Callable[[Self], bool]]) -> Optional[Self]:
        """find the closest ascendant by specified predicate

        Arguments:
            predicate: lambda expression, checking each item for condition, or string representation of expected node

        Returns:
            first matched node or None
        """
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
        """find the closest descendant by specified predicate

        Arguments:
            predicate: lambda expression, checking each item for condition, or string representation of expected node
            depth: amount of levels depth for recursion

        Returns:
            first matched node or None
        """
        return next(self.select(predicate, depth), None)


class UniqueNode(UniNode):
    """Extension to :class:`UniNode` with unique OID and :mod:`weakref` support

    Attributes:
        oid_gen: oid generator
        oid: unique object identifier (usually, within session)
    """
    __slots__ = ['oid', 'oid_gen', '__weakref__']

    def __init__(self, parent: typing.Self = None):
        self.oid_gen = parent.oid_gen if parent else OIDGenerator()
        self.oid = self.oid_gen.gen_id(self)
        super().__init__(parent)


class HTML(str):
    """Mark string as safe HTML content.

    Example::

        refs["message"].set_text(HTML("<h1>Big one</h1>"))
    """

class DynamicDict(dict[str, typing.Any]):
    """Dictionary with dynamic (computable) values.

    It allows to set lambda functions for evaluation and repeated evaluations later::

        x = 2
        d = DynamicDict()
        d["f"] = lambda : x**2
        print(d["f"]) # -> 4
        x = 3
        d.refresh()
        print(d["f"]) # -> 9

    Arguments:
        _lazy_mode (bool): don't evaluate functions at the first assignment
    """
    __slots__ = ['_lazy_mode', '_lambdas']
    def __init__(self, *args, _lazy_mode: bool=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._lambdas: dict[str, typing.Callable[[], typing.Any]] = {}
        self._lazy_mode: bool = _lazy_mode

    def __setitem__(self, key, value):
        if isinstance(value, types.LambdaType) and value.__name__ == '<lambda>':
            self._lambdas[key] = value
            if not self._lazy_mode and key not in self:
                dict.__setitem__(self, key, value())
        else:
            """
            try:
                del self._factories[key]
            except KeyError:
                pass
            """
            dict.__setitem__(self, key, value)

    def __len__(self):
        if '$' in self.keys():
            return dict.__len__(self) - 1
        return dict.__len__(self)

    def items(self):
        for key, value in super().items():
            if key != '$':
                yield key, value

    def refresh(self, attr_name: str | None = None):
        """repeated evaluations

        Affects all functions if `attr_name` is not specified.

        Arguments:
            attr_name (str): attribute name for repeated evaluations.
        """
        if attr_name is None:
            for key, factory_func in self._lambdas.items():
                dict.__setitem__(self, key, factory_func())
        else:
            if attr_name in self._lambdas:
                dict.__setitem__(self, attr_name, self._lambdas[attr_name]())

    def refresh_items(self) -> Iterable[tuple[str, typing.Any]]:
        """iterate through evaluated items only"""
        for key, factory_func in self._lambdas.items():
            yield key, factory_func()

    def __or__(self, other):
        return self.__class__(super().__or__(other))

class DynamicClasses(DynamicDict):
    """Extension to :class:`DynamicDict` to support HTML classes manipulation.

    It allows basic arithmetic operations intuitively::

        c = DynamicClasses("colored bold animated")
        c['selected'] = lambda: True
        c += "hidden"
        c -= "bold"
        c *= "active"
        c *= "active" # switch class on and off again
        print(c) # -> "colored animated selected hidden"
    """
    __slots__ = []
    def __init__(self, *args, **kwargs):
        classes = args[0] if len(args) > 0 else None
        if isinstance(classes, str):
            super().__init__(*args[1:], **kwargs)
            for class_name in classes.split(' '):
                self[class_name] = True
        else:
            super().__init__(*args, **kwargs)

    @staticmethod
    def _check_args(other: str) -> bool | NoReturn:
        if not other:
            return False
        if not isinstance(other, str):
            raise TypeError('Expected string class name to switch on DynamicClasses')
        return True

    def __add__(self, other: str) -> Self:
        if self._check_args(other):
            for class_name in other.split(' '):
                self[class_name] = True
        return self

    def __sub__(self, other: str) -> Self:
        if self._check_args(other):
            for class_name in other.split(' '):
                self[class_name] = False
        return self

    def __mul__(self, other: str) -> Self:
        if self._check_args(other):
            for class_name in other.split(' '):
                self[class_name] = not self.get(class_name, False)
        return self

    def __str__(self):
        base = self.get('$', '')
        return (base + ' ' if base else '') + ' '.join(k for k, v in self.items() if v)

class DynamicStyles(DynamicDict):
    """Extension to :class:`DynamicDict` to support styles parsing

    Example::

        s = DynamicStyles('left: 0; top: 0; width: 100%; height: 100%')
        print(s['left']) # -> "0"
        print(s['width']) # -> "100%"
        s -= "width"
        s["position"] = lambda: "absolute"
        s += "width: 80%"
        print(s) # -> "left: 0; top: 0; height: 100%; width: 80%; position: absolute"
    """
    __slots__ = []
    def __init__(self, style: dict | str | None = None):
        if style:
            if isinstance(style, dict):
                super().__init__(style)
            else:
                super().__init__()
                _ = self + style
        else:
            super().__init__()

    @staticmethod
    def _check_args(other: str) -> bool | NoReturn:
        if not other:
            return False
        if not isinstance(other, str):
            raise TypeError('Expected string style name to switch on DynamicStyles')
        return True

    def __add__(self, style: str) -> Self:
        if self._check_args(style):
            for expr in style.split(';'):
                key, value = expr.split(':', 1)
                self[key.strip()] = value.strip()
        return self

    def __sub__(self, other: str) -> Self:
        if self._check_args(other):
            for class_name in other.split(' '):
                del self[class_name]
        return self

    def __str__(self):
        base = self.get('$', '')
        if isinstance(base, dict):
            return ';'.join(f'{k}: {v}' for k, v in itertools.chain(base.items(), self.items()) if v)
        else:
            return base + ';'.join(f'{k}: {v}' for k, v in self.items() if v)


class ScopeDict(DynamicDict):
    """Extension to :class:`DynamicDict` to support scope variables

    Example::

        layer1 = ScopeDict({'a': 1, 'b': 2})
        layer2 = ScopeDict(layer1)
        layer2['b'] = 3
        layer1['a'] = 5
        print(layer2['a']) # -> 5
        print(layer2['b']) # -> 3
    """
    __slots__ = ['_scope']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._scope: Self = args[0] if len(args) > 0 and isinstance(args[0], ScopeDict) else None

    def __getitem__(self, key: str):
        try:
            return super().__getitem__(key)
        except KeyError:
            if self._scope is None:
                raise
        return self._scope[key]

    def __contains__(self, item):
        return super().__contains__(item) or self._scope and item in self._scope


class WebUnits(str):
    """Helper type to work with `web units <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/length>`__

    This time supports natural arithmetic operations: + - * / //

    Arguments:
        value (int | float | str): numeric value
        unit (str): unit name (px | em | % | ...)
    """
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


def raise_exception_in_thread(thread_id):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print('Exception raise failure')
