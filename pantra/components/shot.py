from __future__ import annotations

import typing
from contextlib import contextmanager
from queue import Queue

if typing.TYPE_CHECKING:
    from .render.render_node import RenderNode

__all__ = ['ContextShot', 'NullContextShot']


class NullContextShot:
    def pop(self):
        raise RuntimeError("Method `pop` not implemented for NullContextShot.")

    def pop_flickering(self):
        raise RuntimeError("Method `pop_flickering` not implemented for NullContextShot.")

    def __call__(self, node):
        pass

    def __add__(self, node):
        return self

    def __sub__(self, other):
        return self


class ContextShot(NullContextShot):
    __slots__ = ['created', 'updated', 'deleted']

    def __init__(self):
        self.created: Queue[RenderNode] = Queue()
        self.updated: Queue[RenderNode] = Queue()
        self.flickering: Queue[RenderNode] = Queue()
        self.deleted: Queue[int] = Queue()

    def pop(self) -> tuple[list[RenderNode], list[RenderNode], list[RenderNode], list[int]]:
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
        flickering = []
        while not self.flickering.empty():
            item = self.flickering.get()
            if item not in deleted and item not in created and item not in updated:
                flickering.append(item)
        return flickering, created, updated, deleted

    def __call__(self, node):
        self.updated.put(node)

    def __add__(self, node):
        self.created.put(node)
        return self

    def __sub__(self, other):
        self.deleted.put(other.oid)
        return self

    def flick(self, node):
        self.flickering.put(node)
