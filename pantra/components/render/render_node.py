from __future__ import annotations

import re
import typing
import logging

from pantra.common import UniqueNode, typename
from ..template import collect_template

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.session import Session
    from ..context import Context, HTMLElement, TextNode
    from ..template import MacroCode, HTMLTemplate
    from ..shot import ContextShotLike

__all__ = ['RenderNode']

RE_JS_VARS = re.compile(r"`?\{\{(.*?)}}`?")
logger = logging.getLogger("pantra.system")

class RenderNode(UniqueNode):
    render_this: ClassVar[bool] = False
    render_if_necessary: ClassVar[bool] = False

    __slots__ = ['context', 'shot', 'session', 'name', 'scope', 'rebind_requested', 'render_this_node']

    def __init__(self, name: str, parent: Optional[RenderNode], shot: Optional[ContextShotLike] = None, session: Optional[Session] = None, context: Optional[Context] = None):
        super().__init__(parent)
        self.shot: ContextShotLike = shot or parent.shot
        self.session: Session = session or parent.session
        self.scope: dict[str, Any] = {} if not parent else parent.scope

        if context:
            self.context: Context = context
        elif parent:
            # slot contents (as well as root contents) belongs to sub-context
            if typename(parent) == 'Context':
                self.context: Context = parent
            else:
                self.context: Context = parent.context
        else:
            self.context: Context = self

        self.name: str = name
        self.rebind_requested: bool = False

        self.render_this_node: bool = self.render_this
        if self.render_this_node:
            self.shot += self

    def __str__(self):
        return self.name or 'unknown'

    def arrange_the_block(self):
        # we have to render control nodes as Stubs to hold middle DOM position
        for i in range(len(self.children)-1):
            node = self.children[i]
            if node.render_if_necessary:
                #and node.context.locals.has_reactions_to(node)):
                node.render_this_node = True
                self.shot += node

    def rebind(self):
        if self.render_this_node:
            self.rebind_requested = True
            self.shot(self)
        else:
            for child in self.children:
                child.rebind()

    def render(self, template: Union[str, HTMLTemplate], locals: dict = None, build: bool = True):
        self.context.renderer(template, self, locals, build)

    def add(self, tag_name: str, attributes: dict = None, text: str = None) -> HTMLElement | Context | None:
        from ..context import HTMLElement
        if tag_name[0].isupper():
            node_template = collect_template(tag_name, self.context.session)
            if not node_template: return None
            return self.render(tag_name, attributes)
        else:
            return HTMLElement(tag_name, self, attributes, text)

    @staticmethod
    def _cleanup_node(node):
        node.context.locals.remove_reactions_to(node)
        if node in node.context.refs.values():
            k = next(k for k, v in node.context.refs.items() if v == node)
            del node.context.refs[k]

    def empty(self) -> Self:
        for child in self.children:  # type: RenderNode
            if child.render_this_node:
                self.shot -= child
            self._cleanup_node(child)
            child.empty()
        self.children.clear()
        return self

    def remove(self, node: Optional[RenderNode] = None):
        if node is not None:
            node.context._cleanup_node(node)
            super().remove(node)
        else:
            self.empty()
            if self.render_this_node:
                self.shot -= self
            self._cleanup_node(self)
            if self.parent:
                self.parent.remove(self)

    def update(self, with_attrs: bool = False):
        if with_attrs:
            self.context.renderer.update(self)
        else:
            self.shot(self)

    def update_tree(self):
        self.context.renderer.update(self, True)

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
        self.scope |= data

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
