from __future__ import annotations

import typing
from contextlib import contextmanager
from queue import Queue

if typing.TYPE_CHECKING:
    from .render.render_node import RenderNode

__all__ = ['ContextShot']


class ContextShot:
    __slots__ = ['created', 'updated', 'deleted', '_frozen', '_freeze_list', '_rebind']

    def __init__(self):
        self.created: Queue[RenderNode] = Queue()
        self.updated: Queue[RenderNode] = Queue()
        self.deleted: Queue[int] = Queue()
        self._frozen = False
        self._rebind = False
        self._freeze_list = None

    def pop(self) -> tuple[list[RenderNode], list[RenderNode], list[int]]:
        deleted = []
        while not self.deleted.empty():
            deleted.append(self.deleted.get())
        created = []
        while not self.created.empty():
            item = self.created.get()
            if item.oid not in deleted:
                created.append(item)
        updated = []
        while not self.updated.empty():
            item = self.updated.get()
            if item.oid not in deleted and item not in created:
                updated.append(item)
        return created, updated, deleted

    @contextmanager
    def freeze(self):
        self._frozen = True
        self._freeze_list = []
        yield
        for node in self._freeze_list:
            node.parent.remove(node)
        self._freeze_list = None
        self._frozen = False

    @contextmanager
    def rebind(self):
        self._rebind = True
        yield
        self._rebind = False

    def __call__(self, node):
        if not self._frozen:
            if self._rebind:
                node._rebind = True
            self.updated.put(node)
        else:
            self._freeze_list.append(node)

    def __add__(self, node):
        if not self._frozen:
            if self._rebind:
                node._rebind = True
            self.created.put(node)
        else:
            self._freeze_list.append(node)
        return self

    def __sub__(self, other):
        self.deleted.put(other.oid)
        return self
