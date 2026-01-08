from __future__ import annotations

import re
import typing
import logging

from pantra.common import UniqueNode, ADict, typename
from ..template import collect_template

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.session import Session
    from ..context import Context, HTMLElement, TextNode
    from ..template import MacroCode, HTMLTemplate
    from ..shot import ContextShot

__all__ = ['RenderNode']

RE_JS_VARS = re.compile(r"`?\{\{(.*?)}}`?")
logger = logging.getLogger("pantra.system")

class RenderNode(UniqueNode):
    __slots__ = ['context', 'shot', 'session', 'render_this', 'name', 'scope', '_rebind']

    def __init__(self, parent: Optional[RenderNode], render_this: bool = False, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        super().__init__(parent)
        self.shot: ContextShot = shot or parent.shot
        self.session: Session = session or parent.session
        self.scope: ADict = ADict() if not parent else parent.scope

        if parent:
            # slot contents (as well as root contents) belongs to sub-context
            if typename(parent) == 'Context':
                self.context: Context = parent
            else:
                self.context: Context = parent.context
        else:
            self.context: Context = self

        def get_first_macro(code_or_list: MacroCode | list[MacroCode]) -> MacroCode:
            return code_or_list[0] if type(code_or_list) is list else code_or_list

        # we have to render control nodes as Stubs to hold middle DOM position
        if not render_this \
                and self.parent \
                and typename(self) in ('ConditionNode', 'LoopNode') \
                and get_first_macro(self.template[0].macro).reactive \
                and self.index() < len(self.template.parent.children) - 1:
                    self.render_this = True
                    # and (self.template[-1].tag_name == '#else' \
                    #    or self.index() < len(self.template.parent.children) - 1):
        else:
            self.render_this: bool = render_this

        if self.render_this:
            self.shot += self

        self.name = ''
        self._rebind = False

    def render(self, template: Union[str, HTMLTemplate], locals: dict = None, build: bool = True):
        self.context.renderer(template, self, locals, build)

    def add(self, tag_name: str, attributes: dict = None, text: str = None) -> HTMLElement | Context | None:
        from ..context import HTMLElement
        if tag_name[0].isupper():
            node_template = collect_template(tag_name, self.context.session)
            if not node_template: return None
            return self.context.render(node_template, self, locals=attributes)
        else:
            return HTMLElement(tag_name, self, attributes, text)

    @staticmethod
    def _cleanup_node(node):
        if node in node.context.react_nodes:
            node.context.react_nodes.remove(node)
            for v in list(node.context.react_vars.values()):
                if node in v:
                    v.remove(node)
        if node in node.context.refs.values():
            k = next(k for k, v in node.context.refs.items() if v == node)
            del node.context.refs[k]

    def empty(self):
        for child in self.children:  # type: RenderNode
            if child.render_this:
                self.shot -= child
            self._cleanup_node(child)
            child.empty()
        self.children.clear()

    def remove(self, node: Optional[RenderNode] = None):
        if node is not None:
            node.context._cleanup_node(node)
            super().remove(node)
        else:
            self.empty()
            if self.render_this:
                self.shot -= self
            self._cleanup_node(self)
            if self.parent:
                self.parent.remove(self)

    def update(self, with_attrs: bool = False):
        if with_attrs:
            self.context.render.update(self)
        else:
            self.shot(self)

    def update_tree(self):
        self.context.renderer.update(self, True)

    def rebuild(self):
        self.empty()
        self.renderer.build()

    def _clone(self, new_parent: RenderNode) -> Optional[HTMLElement, TextNode]:
        return None

    def clone(self, new_parent: Optional[RenderNode] = None) -> Optional[HTMLElement, TextNode]:
        if new_parent is None:
            new_parent = self.context

        clone = self._clone(new_parent)
        if clone:
            for child in self.children:
                sub = child.clone(clone)
                if sub:
                    clone.append(sub)
        return clone

    def select(self, predicate: Union[str, Iterable[str], Callable[[RenderNode], bool]], depth: int = None) -> Generator[RenderNode]:
        if isinstance(predicate, str):
            yield from super().select(lambda node: str(node) == predicate, depth)
        elif isinstance(predicate, typing.Iterable):
            yield from super().select(lambda node: str(node) in predicate, depth)
        else:
            yield from super().select(predicate, depth)

    def contains(self, predicate: Union[str, Iterable[str], Callable[[RenderNode], bool]], depth: int = None) -> bool:
        return next(self.select(predicate, depth), None) is not None

    def set_scope(self, data: Union[Dict, str], value: Any = None):
        if isinstance(data, str):
            data = {data: value}
        self.scope = ADict(self.scope) | data

    def describe(self, indent: int = 0) -> str:
        res = ' ' * indent + str(self) + ':' + str(self.oid)
        for c in self.children:
            res += '\n' + ' ' * indent + c.describe(indent + 2)
        return res

    def kill_task(self, func_name: str | Callable):
        if callable(func_name):
            func_name = func_name.__name__
        self.session.kill_task(f'{self.oid}#{func_name}')

    def kill_all_tasks(self):
        self.session.kill_all_tasks(self)
