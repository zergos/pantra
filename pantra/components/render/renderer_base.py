from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from contextlib import contextmanager

from pantra.common import DynamicString, DynamicValue
from pantra.compiler import ContextInitFailed
from ..template import MacroCode, MacroType

if typing.TYPE_CHECKING:
    from typing import Callable, Any, Union, Optional
    from ..context import Context, HTMLElement
    from ..template import HTMLTemplate, AttrType
    from .render_node import RenderNode

StrOrCode = str | MacroCode | None

__all__ = ['RendererBase', 'StrOrCode']

class RendererBase(ABC):
    __slots__ = ['ctx', 'in_builder']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx
        self.in_builder: bool = False

    def __call__(self, template: str | HTMLTemplate, parent: RenderNode = None, locals: dict = None, build: bool = True):
        return self.render(template, parent, locals, build)

    @contextmanager
    def builder_context(self):
        self.in_builder = True
        yield
        self.in_builder = False

    def build(self):
        try:
            with self.builder_context():
                self.build_node(self.ctx.template, self.ctx)
        except ContextInitFailed:
            self.ctx.remove()

    def eval_value(self, macro: MacroCode, node: RenderNode, bind_ctx: Context = None):
        ctx = bind_ctx or self.ctx
        if type(macro.code) == list:
            if len(macro.code) == 1:
                return ctx.locals[macro.code[0]]
            value = ctx.locals
            for chunk in macro.code:
                value = getattr(value, chunk)
            return value
        else:
            return eval(macro.code, {'ctx': ctx, 'this': node}, ctx.locals)

    def trace_eval(self, macro: MacroCode, node: RenderNode, bind_ctx: Context = None):
        ctx = bind_ctx or self.ctx
        with ctx.session.node_context(node):
            if self.in_builder and macro.reactive:
                with ctx.record_reactions(node):
                    return self.eval_value(macro, node, ctx)
            else:
                return self.eval_value(macro, node, ctx)

    def translate(self, s):
        if s.startswith('\\'):
            return s[1:]
        if s.startswith('#'):
            return self.ctx.session.gettext(s[1:])
        return s

    def build_value(self, source: StrOrCode, node: RenderNode, bind_ctx: Context = None) -> Any:
        ctx = bind_ctx or self.ctx
        if isinstance(source, str):
            if source.startswith('@'):
                return ctx[source[1:]]
            return self.translate(source)
        if type(source) is MacroCode:
            value = self.trace_eval(source, node, ctx)
            if source.type == MacroType.STRING:
                return value or ''
            return value
        return source

    def build_func(self, source: StrOrCode, node: RenderNode) -> Callable[[], Any]:
        ctx = self.ctx  # save ctx to lambda instead of self, as ctx could be temporarily changed by slot
        if isinstance(source, str):
            return lambda: ctx[source]
        if type(source) is MacroCode:
            if source.type == MacroType.STRING:
                return lambda: self.trace_eval(source, node, ctx) or ''
            else:
                return lambda: self.trace_eval(source, node, ctx)
        raise ValueError("Can't build a function with raw value")

    def dynamic_string(self, source: StrOrCode, node: RenderNode) -> str | DynamicString:
        if type(source) is MacroCode:
            return DynamicString(self.build_func(source, node))
        return source

    def dynamic_value(self, source: Any | MacroCode, node: RenderNode) -> Any | DynamicValue:
        if type(source) is MacroCode:
            return DynamicValue(self.build_func(source, node))
        return source

    def dynamic_string_i10n(self, source: StrOrCode, node: RenderNode) -> str | DynamicString:
        if type(source) is MacroCode:
            return DynamicString(self.build_func(source, node))
        return self.translate(source)

    """
    def eval_string(self, source: StrOrCode, node: RenderNode) -> Any:
        if type(source) is MacroCode:
            return self.trace_eval(source, node)
        return source

    def eval_string_i10n(self, source: StrOrCode, node: RenderNode) -> Any:
        if source is None:
            return None

        if type(source) is MacroCode:
            return self.trace_eval(source, node)
        return self.translate(source)

    def build_func_or_local(self, source: StrOrCode, node: RenderNode, default: Any = None) -> Callable[[], Any]:
        if type(source) is MacroCode:
            return self.build_func(source, node)
        else:
            ctx = self.ctx
            return lambda: ctx.locals.get(source, default)
    """

    @abstractmethod
    def process_special_attribute_html(self, attr: tuple[AttrType, str | None], value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        ...

    @abstractmethod
    def process_special_attribute_ctx(self, attr: tuple[AttrType, str | None], value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        ...

    @abstractmethod
    def build_node(self, template: HTMLTemplate, parent: Optional[RenderNode] = None) -> Optional[RenderNode]:
        ...

    def rebind(self, node: RenderNode):
        if node.render_this:
            self.ctx.shot(node)
        else:
            for child in node.children:
                self.rebind(child)

    def update_children(self, node: RenderNode):
        for child in node.children:  # type: RenderNode
            if child.context == self.ctx:
                self.update(child, True)
            else:
                child.update_tree()

    @abstractmethod
    def update(self, node: RenderNode, recursive: bool = False):
        ...

    def render(self, template: Union[str, HTMLTemplate], parent: RenderNode = None, locals: dict = None, build: bool = True):
        from ..context import Context
        if not parent:
            parent = self.ctx
        c = Context(template, parent, locals=locals)
        if build:
            c.renderer.build()
        return c
