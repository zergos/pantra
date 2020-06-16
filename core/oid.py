from __future__ import annotations

import typing
from itertools import count
import weakref

if typing.TYPE_CHECKING:
    from .common import AnyNode


def gen_id(obj: AnyNode) -> int:
    get_node.list.append(weakref.ref(obj))
    return next(gen_id.counter)
gen_id.counter = count()


def get_node(oid: int) -> AnyNode:
    return get_node.list[oid]() if oid < len(get_node.list) else None
get_node.list: typing.List[weakref.ReferenceType] = []


'''
import ctypes

gen_id = id


def get_object(oid):
    return ctypes.cast(oid, ctypes.py_object).value
'''
