from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass

from pantra.common import DynamicString, DynamicValue
from pantra.compiler import ContextInitFailed
from ..template import MacroCode, MacroType
from ..context import HTMLElement, Slot

if typing.TYPE_CHECKING:
    from typing import *
    from types import CodeType
    from pantra.session import Session
    from ..context import Context
    from ..template import HTMLTemplate, AttrType
    from .render_node import RenderNode

StrOrCode = str | MacroCode | None

__all__ = ['RendererBase', 'StrOrCode', 'ForLoopType']

@dataclass(slots=True)
class ForLoopType:
    parent: Self
    counter: int = 0
    counter0: int = 0
    index: Hashable = 0


class RendererBase(ABC):
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

    def __call__(self, template: str | HTMLTemplate, parent: RenderNode = None, locals: dict = None, build: bool = True):
        return self.render(template, parent, locals, build)

    @classmethod
    @abstractmethod
    def collect_template(cls, name: str, session: Optional[Session] = None, app: Optional[str] = None) -> Optional[HTMLTemplate | CodeType]:
        ...

    def add(self, tag_name: str, parent: RenderNode) -> HTMLElement:
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
        try:
            self.build_node(self.ctx.template, self.ctx)
        except ContextInitFailed:
            self.ctx.remove()

    def trace_eval(self, macro: MacroCode, node: RenderNode, bind_ctx: Context = None):
        ctx = bind_ctx or self.ctx
        with ctx.session.node_context(node):
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
            else:
                return eval(macro.code, {'ctx': ctx, 'this': node}, ctx.locals)

    def translate(self, s: str) -> str:
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
            if source.reactive:
                ctx.locals.register_reactions(source.vars, node)
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
            if source.reactive:
                ctx.locals.register_reactions(source.vars, node)
            if source.type == MacroType.STRING:
                return lambda: self.trace_eval(source, node, ctx) or ''
            else:
                return lambda: self.trace_eval(source, node, ctx)
        raise ValueError("Can't build a function with raw value")

    def build_string_or_func(self, source: StrOrCode, node: RenderNode) -> str | Callable[[], Any]:
        if isinstance(source, str):
            if source.startswith('@'):
                return self.build_func(source[1:], node)
            return self.translate(source)
        return self.build_func(source, node)

    def dynamic_string(self, source: StrOrCode, node: RenderNode) -> str | DynamicString:
        if type(source) is MacroCode:
            return DynamicString(self.build_func(source, node))
        return source

    def dynamic_value(self, source: Any | MacroCode, node: RenderNode) -> Any | DynamicValue:
        if type(source) is MacroCode:
            return DynamicValue(self.build_func(source, node))
        return self.translate(source)

    def dynamic_string_i10n(self, source: StrOrCode, node: RenderNode) -> str | DynamicString:
        if type(source) is MacroCode:
            return DynamicString(self.build_func(source, node))
        return self.translate(source)

    @abstractmethod
    def build_node(self, template: HTMLTemplate, parent: Optional[RenderNode] = None) -> Optional[RenderNode]:
        ...

    def update_children(self, node: RenderNode):
        for child in node.children:  # type: RenderNode
            if child.context == self.ctx:
                self.update(child, True)
            else:
                child.update_tree()

    @abstractmethod
    def update(self, node: RenderNode, recursive: bool = False):
        ...

    def render(self, template: str | HTMLTemplate | CodeType, parent: RenderNode = None, locals: dict = None, build: bool = True):
        from ..context import Context
        if not parent:
            parent = self.ctx
        c = Context(template, parent, locals=locals)
        if build:
            c.renderer.build()
        return c
