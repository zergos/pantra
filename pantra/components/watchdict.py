from __future__ import annotations
import typing
from pantra.common import ADict

if typing.TYPE_CHECKING:
    from pantra.components.context import Context, AnyNode
    from typing import *


class WatchDict(ADict):
    def __init__(self, ctx: Union[Context, WatchDict]):
        if type(ctx) == WatchDict:
            super().__init__(ctx)
            self._ctx = ctx._ctx
        else:
            super().__init__()
            self._ctx = ctx
        self._node = None

    def __setattr__(self, key, value):
        if key[0] == '_':
            object.__setattr__(self, key, value)
            return
        if key not in self:
            self[key] = value
            return

        old_value = self[key]
        self[key] = value
        if value != old_value and key in self._ctx.react_vars:
            for node in frozenset(self._ctx.react_vars[key]):
                node.update(True)


class WatchDictActive(WatchDict):
    def start_record(self, node: AnyNode):
        self._node = node

    def stop_record(self):
        self._node = None

    def _record(self, item):
        self._ctx.react_vars[item].add(self._node)
        self._ctx.react_nodes.add(self._node)

    def __getitem__(self, item):
        res = super().__getitem__(item)
        if self._node and item[0] != '_':
            self._record(item)
        return res

    def get(self, item, default=None):
        res = super().get(item, default)
        if self._node and item[0] != '_':
            self._record(item)
        return res

