from __future__ import annotations
import typing
from collections import defaultdict

from ..common import typename
from .controllers import process_call

if typing.TYPE_CHECKING:
    from .render.render_node import RenderNode
    from .context import ReactNode

class ReactDict(dict):
    __slots__ = ('react_vars', 'react_nodes')

    def __init__(self):
        super().__init__()
        self.react_vars: dict[str, set[RenderNode]] = defaultdict(set)
        self.react_nodes: set[RenderNode] = set()

    def call(self, func_name, *args, **kwargs):
        self[func_name](*args, **kwargs)

    def register_reactions(self, var_names: set[str], node: RenderNode):
        for var_name in var_names:
            self.react_vars[var_name].add(node)
        self.react_nodes.add(node)

    def remove_reactions_to(self, node: RenderNode):
        if node in self.react_nodes:
            self.react_nodes.remove(node)
            for v in self.react_vars.values():
                v.discard(node)

    def has_reactions_to(self, node: RenderNode) -> bool:
        return node in self.react_nodes

    def __setitem__(self, key, value):
        if key not in self:
            dict.__setitem__(self, key, value)
            return

        old_value = self[key]
        dict.__setitem__(self, key, value)
        if (nodes:=self.react_vars.get(key, None)) is not None and value != old_value:
            copy = nodes.copy()
            for node in nodes: # type: ReactNode
                # WARNING: `nodes` list is dynamically changed by updates, but we need to avoid new nodes
                # as well as deleted ones
                if node not in copy:
                    continue
                if typename(node) == 'ReactNode':
                    node.value = value
                    process_call(node.context.session, node.context, node.action, node)
                else:
                    node.update(True)

    def set_quietly(self, key, value):
        super().__setitem__(key, value)

    def __str__(self):
        return ', '.join(self.keys())
