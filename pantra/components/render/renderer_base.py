from __future__ import annotations

import traceback
import typing
from abc import ABC, abstractmethod

from pantra.common import DynamicString
from pantra.compiler import ContextInitFailed
from ..template import MacroCode

if typing.TYPE_CHECKING:
    from typing import Callable, Any, Union, Optional
    from pantra.components.context import Context, HTMLElement, AnyNode
    from pantra.components.template import HTMLTemplate, AttrType

StrOrCode = str | MacroCode | None

__all__ = ['RendererBase', 'StrOrCode']

class RendererBase(ABC):
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

    def __call__(self, template: str | HTMLTemplate, parent: AnyNode = None, locals: dict = None, build: bool = True):
        return self.render(template, parent, locals, build)

    def build(self):
        try:
            self.build_node(self.ctx.template, self.ctx)
        except ContextInitFailed:
            self.ctx.remove()

    def trace_eval(self, ctx: Context, macro: MacroCode, node: AnyNode):
        try:
            with self.ctx.record_reactions(node, macro.reactive):
                return eval(macro.code, {'ctx': ctx, 'this': node}, ctx.locals)
        except:
            ctx.session.error(f'{ctx.template.path()}/{node}: evaluation error: {traceback.format_exc(-3)}')
            return None

    def build_func(self, macro: MacroCode | None, node: AnyNode) -> Callable[[], Any] | None:
        # return lambda: eval(text, {'ctx': self.ctx, 'this': node}, self.ctx.locals)
        ctx = self.ctx  # save ctx to lambda instead of self, as ctx could be temporarily changed by slot
        return macro and (lambda: self.trace_eval(ctx, macro, node))

    def translate(self, s):
        if s.startswith('\\'):
            return s[1:]
        if s.startswith('#'):
            return self.ctx.session.gettext(s[1:])
        return s

    def build_string(self, source: StrOrCode, node: AnyNode) -> str | DynamicString | None:
        if type(source) is MacroCode:
            return DynamicString(self.build_func(source, node))
        return source

    def build_string_i10n(self, source: StrOrCode, node: AnyNode) -> str | DynamicString | None:
        if source is None:
            return None
        if type(source) is MacroCode:
            return DynamicString(self.build_func(source, node))
        return self.translate(source)

    def eval_string(self, source: StrOrCode, node: AnyNode) -> Any:
        if type(source) is MacroCode:
            return self.trace_eval(self.ctx, source, node)
        return source

    def eval_string_i10n(self, source: StrOrCode, node: AnyNode) -> Any:
        if source is None:
            return None

        if type(source) is MacroCode:
            return self.trace_eval(self.ctx, source, node)
        if source.startswith('@'):
            if ' ' in source:
                callers = [self.ctx[var] for var in source[1:].split(' ')]
                return lambda *args: [caller(*args) for caller in callers]
            return self.ctx[source[1:]]
        return self.translate(source)

    def build_func_or_local(self, source: StrOrCode, node: AnyNode, default: Any = None) -> Callable[[], Any]:
        if type(source) is MacroCode:
            return self.build_func(source, node)
        else:
            ctx = self.ctx
            return lambda: ctx.locals.get(source, default)

    @abstractmethod
    def process_special_attribute_html(self, attr: tuple[AttrType, str | None], value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        ...

    @abstractmethod
    def process_special_attribute_ctx(self, attr: tuple[AttrType, str | None], value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        ...

    @abstractmethod
    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode] = None) -> Optional[AnyNode]:
        ...

    def rebind(self, node: AnyNode):
        if node.render_this:
            self.ctx.shot(node)
        else:
            for child in node.children:
                self.rebind(child)

    def update_children(self, node: AnyNode):
        for child in node.children:  # type: AnyNode
            if child.context == self.ctx:
                self.update(child, True)
            else:
                child.update_tree()

    @abstractmethod
    def update(self, node: AnyNode, recursive: bool = False):
        ...

    def render(self, template: Union[str, HTMLTemplate], parent: AnyNode = None, locals: dict = None, build: bool = True):
        from ..context import Context
        if not parent:
            parent = self.ctx
        c = Context(template, parent, locals=locals)
        if build:
            c.renderer.build()
        return c

