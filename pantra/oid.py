from __future__ import annotations

import typing
from itertools import count
import weakref

if typing.TYPE_CHECKING:
    from pantra.components.render.render_node import RenderNode


def gen_id(obj: RenderNode) -> int:
    idx = next(gen_id.counter)
    get_node.oids[idx] = obj
    return idx
gen_id.counter = count()


def get_node(oid: int) -> RenderNode:
    return get_node.oids.get(oid)
get_node.oids: weakref.WeakValueDictionary[int, typing.Any] = weakref.WeakValueDictionary()


'''
import ctypes

gen_id = id


def get_object(oid):
    return ctypes.cast(oid, ctypes.py_object).value
'''
