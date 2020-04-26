from anytree import NodeMixin
from typing import *

__all__ = ['UniNode', 'DynamicString', 'DynamicClasses']


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

    def __str__(self):
        return self.__class__.__name__

    def __getitem__(self, item):
        return self._NodeMixin__children[item]


class DynamicString(str):
    __slots__ = ['func']

    def __new__(cls, func: Callable[[], str]):
        return super().__new__(cls, func())

    def __init__(self, func: Callable[[], str]):
        self.func: Callable[[], str] = func

    def __call__(self, *args, **kwargs) -> 'DynamicString':
        return DynamicString(self.func)

    def __add__(self, other):
        if not other:
            return DynamicString(self.func)
        return self+other


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