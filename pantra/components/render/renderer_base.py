from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass

from pantra.compiler import ContextInitFailed
from ..template import MacroCode
from ..context import HTMLElement, Slot

if typing.TYPE_CHECKING:
    from typing import *
    from types import CodeType
    from pantra.session import Session
    from ..context import Context
    from ..template import HTMLTemplate
    from .render_node import RenderNode

ValueOrCode = typing.Any | MacroCode

__all__ = ['RendererBase', 'ValueOrCode', 'ForLoopType']

@dataclass(slots=True)
class ForLoopType:
    parent: Self
    counter: int = 0
    counter0: int = 0
    index: Hashable = 0


class RendererBase(ABC):
    """Renderer base class

    Attributes:
        ctx: Local context of component
        templates: (class variable) dictionary of all loaded templates
    """

    templates: ClassVar[dict[str, Any]] = {}
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

    @classmethod
    @abstractmethod
    def collect_template(cls, name: str, session: Optional[Session] = None, app: Optional[str] = None) -> Optional[HTMLTemplate | CodeType]:
        """Abstract method to collect component's template by given name

        Arguments:
            name: component name
            session: Optional session instance, used for loading feedback messages
            app: Optional application instance if session is not defined

        Returns:
            :class:`HTMLTemplate` or factory
        """

    def add(self, tag_name: str, parent: RenderNode) -> HTMLElement:
        """Add HTML element with specified tag to this context.

        Arguments:
            tag_name: tag name ("div", "p", etc.)
            parent: parent node inside this context, if specified
        """
        node = HTMLElement(tag_name, parent, context=self.ctx)
        return node

    @contextmanager
    def override_ns_type(self, slot: Slot):
        if self.ctx.ns_type:
            save_ns_type = slot.ctx.ns_type
            slot.ctx.ns_type = self.ctx.ns_type
            yield
            slot.ctx.ns_type = save_ns_type
        else:
            yield

    def build(self):
        """Build this node by associated template and prepare for continues rendering"""
        try:
            self.build_node(self.ctx.template, self.ctx)
        except ContextInitFailed:
            self.ctx.remove()

    def trace_eval(self, macro: MacroCode, node: RenderNode, bind_ctx: Context = None):
        ctx = bind_ctx or self.ctx
        with ctx.session.node_context(node):
            if isinstance(macro.code, str):
                return ctx.locals[macro.code]
            if type(macro.code) == list:
                var_name = macro.code[0]
                if len(macro.code) == 1:
                    return ctx.locals[var_name]
                if var_name == 'ctx':
                    value = ctx
                elif var_name == 'this':
                    value = node
                else:
                    value = ctx.locals[var_name]
                for chunk in macro.code[1:]:
                    value = getattr(value, chunk)
                return value
            return eval(macro.code, {'ctx': ctx, 'this': node}, ctx.locals)

    def makeup_value(self, source: ValueOrCode, node: RenderNode, evaluate_once: bool = False) -> Any:
        ctx = self.ctx  # save ctx to lambda instead of self, as ctx could be temporarily changed by slot
        if type(source) is MacroCode:
            if evaluate_once or source.evaluated:
                return self.trace_eval(source, node, ctx)
            if source.reactive:
                ctx.locals.register_reactions(source.vars, node)
            return lambda: self.trace_eval(source, node, ctx)
        else:
            return source

    @abstractmethod
    def build_node(self, template: Any, parent: Optional[RenderNode] = None) -> Optional[RenderNode]:
        """Build child node from given template within current context

        Note:
            Not necessary to call this method directly. Use :meth:`build` and :meth:`render` instead.

        Arguments:
            template: template node or factory
            parent: parent node inside this context, if specified
        """

    def update_children(self, node: RenderNode):
        """Update all child nodes recursively

        Arguments:
            node: node to update
        """
        for child in node.children:  # type: RenderNode
            if child.context == self.ctx:
                self.update(child, True)
            else:
                child.update_tree()

    @abstractmethod
    def update(self, node: RenderNode, recursive: bool = False):
        """Update rendered node, to sync changes

        Arguments:
            node: node to update
            recursive: update children recursively
        """

    def render(self,
               template: str | HTMLTemplate | CodeType,
               parent: RenderNode = None,
               locals: dict = None,
               build: bool = True):
        """Render new node.

        Arguments:
            template: template to render or code
            parent: parent node inside this context, if specified
            locals: locals dict for current context
            build: whether to build the node
        """
        from ..context import Context
        if not parent:
            parent = self.ctx
        c = Context(template, parent, locals=locals)
        if build:
            c.renderer.build()
        return c
