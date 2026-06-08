from __future__ import annotations

import typing

from pantra.common import UniqueNode, typename, DynamicDict, ScopeDict
from ..template import collect_template

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.session import Session
    from ..context import Context, HTMLElement, TextNode
    from ..template import HTMLTemplate
    from ..shot import ContextShotLike, ContextShot

__all__ = ['RenderNode']

class RenderNode(UniqueNode):
    """Base class for rendered nodes (extension to :class:`UniqueNode`).

    Attributes:
        context (Context): reference to main component context
        shot (ContextShot): snapshot manager to update changes
        session (Session): reference to current session
        scope (DynamicDict): reference to the :ref:`scope <scope>`
        rebind_requested (bool): whether this node should be rebound to another parent
        render_this_node (bool): whether this node should be rendered
    """
    render_this: ClassVar[bool] = False

    __slots__ = ['context', 'shot', 'session', '_scope', 'rebind_requested', 'render_this_node']

    def __init__(self, parent: Optional[RenderNode], shot: Optional[ContextShotLike] = None, session: Optional[Session] = None, context: Optional[Context] = None):
        super().__init__(parent)
        self.shot: ContextShotLike = shot or parent.shot
        self.session: Session = session or parent.session
        self._scope: Optional[DynamicDict] = None

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

        self.rebind_requested: bool = False

        self.render_this_node: bool = self.render_this
        if self.render_this_node:
            self.shot += self

    @property
    def scope(self) -> ScopeDict:
        if self._scope is None:
            if self.parent:
                self._scope = ScopeDict(self.parent.top_most_scope)
            else:
                self._scope = ScopeDict()
        return self._scope

    @property
    def top_most_scope(self) -> ScopeDict:
        """get parent scope or this one"""
        if self._scope is None:
            if self.parent:
                return self.parent.top_most_scope
            else:
                self._scope = ScopeDict()
        return self._scope

    def __str__(self):
        return 'node'

    def rebind(self):
        """request rebind for this node after parent changed"""
        if self.render_this_node:
            self.rebind_requested = True
            self.shot(self)
        else:
            for child in self.children:
                child.rebind()

    def render(self, template: Union[str, HTMLTemplate], locals: dict = None, build: bool = True):
        """render new child node.

        Arguments:
            template: template to render or code
            locals: locals dict for current context
            build: whether to build the node
        """
        self.context.renderer.render(template, self, locals, build)

    def add(self, tag_name: str, attributes: dict = None, text: str = None) -> HTMLElement | Context | None:
        """add and render component context or HTML element

        Arguments:
            tag_name: tag name (lowercase for HTML node)
            attributes: attributes to set
            text: text to set

        Returns:
            added node
        """
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
        """remove all child nodes"""
        for child in self.children:  # type: RenderNode
            if child.render_this_node:
                self.shot -= child
            self._cleanup_node(child)
            child.empty()
        self.children.clear()
        return self

    def remove(self, node: Optional[RenderNode] = None):
        """remove this or specified node"""
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
        """send node changes to the client-side

        Arguments:
            with_attrs: whether to update dynamic attributes
        """
        if with_attrs:
            self.context.renderer.update(self)
        else:
            self.shot(self)

    def update_tree(self):
        """update and send this node and all its children"""
        self.context.renderer.update(self, True)

    def _frozen_clone(self, new_parent: RenderNode) -> Optional[HTMLElement, TextNode]:
        return None

    def frozen_clone(self, new_parent: Optional[RenderNode] = None) -> Optional[HTMLElement, TextNode]:
        """make visual copy of the node and all its children

        Visual copy means - all dynamic nodes become static, freezing last states and values

        Arguments:
            new_parent: optionally, new parent node

        Returns:
            new node
        """
        if new_parent is None:
            new_parent = self.context

        clone = self._frozen_clone(new_parent)
        if clone:
            for child in self.children:
                sub = child.frozen_clone(clone)
                if sub:
                    clone.append(sub)
        return clone

    def select(self, predicate: Union[str, Iterable[str], Callable[[RenderNode], bool]], depth: int = None) -> Generator[RenderNode]:
        """select all nodes by condition

        Arguments:
            predicate: lambda function, string representation of list of string representations
            depth: depth of selection

        Yields:
            selected node
        """
        if isinstance(predicate, str):
            yield from super().select(lambda node: str(node) == predicate, depth)
        elif isinstance(predicate, typing.Iterable):
            yield from super().select(lambda node: str(node) in predicate, depth)
        else:
            yield from super().select(predicate, depth)

    def contains(self, predicate: Union[str, Iterable[str], Callable[[RenderNode], bool]], depth: int = None) -> bool:
        """check if node is contained by predicate

        Arguments are similar to :meth:`select`
        """
        return next(self.select(predicate, depth), None) is not None

    def kill_task(self, func_name: str | Callable):
        """kill running task by context OID and function name

        Read more: :doc:`session tasks <session_tasks>`
        """
        if callable(func_name):
            func_name = func_name.__name__
        self.session.kill_task(f'{self.oid}#{func_name}')

    def kill_all_tasks(self):
        """kill all running tasks in this context"""
        self.session.kill_all_tasks(self)
