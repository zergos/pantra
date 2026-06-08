from __future__ import annotations

import typing
from itertools import count
import weakref

if typing.TYPE_CHECKING:
    from pantra.common import UniqueNode
    from pantra.components.render.render_node import RenderNode


class OIDGenerator:
    __slots__ = ('counter', 'oids')

    def __init__(self):
        self.counter = count()
        self.oids: weakref.WeakValueDictionary[int, typing.Any] = weakref.WeakValueDictionary()

    def gen_id(self, obj: UniqueNode) -> int:
        idx = next(self.counter)
        self.oids[idx] = obj
        return idx

    def get_node(self, oid: int) -> RenderNode:
        return self.oids.get(oid)


'''
import ctypes

gen_id = id


def get_object(oid):
    return ctypes.cast(oid, ctypes.py_object).value
'''
