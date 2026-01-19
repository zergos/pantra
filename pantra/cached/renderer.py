from __future__ import annotations

import typing
import logging

from pantra.components.render.renderer_base import RendererBase, ForLoopType
from pantra.components.render.renderer_html import RendererHTML
from pantra.common import typename
from pantra.components.template import HTMLTemplate
from pantra.components.context import HTMLElement, NSElement
from pantra.settings import config

if typing.TYPE_CHECKING:
    from typing import *
    from types import CodeType
    from pantra.session import Session
    from pantra.components.context import Condition, LoopNode
    from pantra.components.render.render_node import RenderNode

logger = logging.getLogger("pantra.system")

class RendererCached(RendererBase):
    templates: ClassVar[dict[str, CodeType]] = {}
    __slots__ = ()

    @classmethod
    def collect_template(cls, name: str, session: Optional[Session] = None, app: Optional[str] = None) -> Optional[CodeType]:
        app = session and session.app or app
        key = app + '/' + name if app is not None else name
        if key in cls.templates:
            return cls.templates[key]

        if app:
            module_file_name = (config.CACHE_PATH / 'apps' / app / name).with_suffix('.py')
            if not module_file_name.exists():
                module_file_name = (config.CACHE_PATH / 'core' / name).with_suffix('.py')
                if not module_file_name.exists():
                    return None
        else:
            module_file_name = (config.CACHE_PATH / 'core' / name).with_suffix('.py')
            if not module_file_name.exists():
                return None

        code = compile(module_file_name.read_text(encoding='utf-8'), str(module_file_name), 'exec')
        cls.templates[name] = code
        return code

    def build_node(self, template: HTMLTemplate, parent: Optional[RenderNode] = None) -> Optional[RenderNode]:
        raise NotImplementedError()

    def build(self):
        if self.__class__ is RendererCached:
            initial_locals = {k: v for k, v in self.ctx.locals.items() if k not in ('init', 'on_restart', 'ctx', 'refs')}
            common_locals = {'ctx': self.ctx, 'refs': self.ctx.refs, 'session': self.ctx.session, '_': self.ctx.session.gettext, 'logger': logger}
            self.ctx.locals.update(common_locals)
            exec(self.ctx.template, self.ctx.locals)
            self.ctx.locals.update(initial_locals)
            self.__class__ = self.ctx.locals[f'{self.ctx.name}Renderer']
        self.build_node(self.ctx.template, self.ctx)

    def arrange_the_block(self, node):
        node.render_this_node = True
        self.ctx.shot += node

    #region Node updaters
    def _update_condition_node(self, node, recursive):
        state: int
        condition: Optional[Condition]
        for i, c in enumerate(node.conditions):
            if c.func():
                state = i
                condition = c
                break
        else:
            state = -1
            condition = None

        if node.state != state:
            if node.state >= 0:
                node.empty()
            node.state = state
            if state == -1:
                return False

            condition.template(node)

            return False
        return True

    def _update_loop_node(self, node: LoopNode, recursive):
        if not node.index_func:
            node.empty()
            empty = True
            iter = node.iterator()
            if iter:
                parentloop = self.ctx.locals.get('forloop')
                for_loop = ForLoopType(parentloop)
                self.ctx.locals['forloop'] = for_loop
                for i, value in enumerate(iter):
                    empty = False
                    for_loop.counter = i + 1
                    for_loop.counter0 = i
                    node.loop_template(node, for_loop, value)
                if parentloop:
                    self.ctx.locals['forloop'] = parentloop
                else:
                    del self.ctx.locals['forloop']
        else:
            empty = not node.index_map
            if empty:
                node.empty()
            iter = node.iterator()
            if iter:
                oldmap = node.index_map
                node.index_map = newmap = {}

                pos = 0
                parentloop = self.ctx.locals.get('forloop')
                for_loop = ForLoopType(parentloop)
                self.ctx.locals['forloop'] = for_loop
                for i, value in enumerate(iter):
                    for_loop.counter = i + 1
                    for_loop.counter0 = i
                    index = node.index_func(for_loop, value)
                    for_loop.index = index
                    if index in oldmap:
                        for sub in oldmap[index]:  # type: RenderNode
                            sub.move(pos)
                            sub.rebind()
                            pos += 1
                        newmap[index] = oldmap[index]
                        del oldmap[index]
                    else:
                        newmap[index] = []
                        last_child_idx = len(node.children)
                        node.loop_template(node, for_loop, value)
                        for k in range(last_child_idx, len(node.children)):
                            sub = node.children[k]
                            sub.move(pos)
                            newmap[index].append(sub)
                            pos += 1
                if parentloop:
                    self.ctx.locals['forloop'] = parentloop
                else:
                    del self.ctx.locals['forloop']
                for lst in oldmap.values():
                    for sub in lst:
                        sub.remove()
                    lst.clear()
                empty = not node.index_map

        if empty and node.else_template:
            node.else_template(node)

        return False

    def _update_set_node(self, node, recursive):
        node.empty()
        value = node.value()
        node.template(node, value)
        return False

    NODE_UPDATERS: dict[str, Callable[[Self, RenderNode, bool], bool]] = {
        'HTMLElement': RendererHTML._update_html_node,
        'NSElement': RendererHTML._update_html_node,
        'Context': RendererHTML._update_context_node,
        'TextNode': RendererHTML._update_text_node,
        'ConditionNode': _update_condition_node,
        'LoopNode': _update_loop_node,
        'SetNode': _update_set_node,
    }
    #endregion

    def update(self, node: RenderNode, recursive: bool = False):
        if self.NODE_UPDATERS[typename(node)](self, node, recursive) and recursive:
            self.update_children(node)
