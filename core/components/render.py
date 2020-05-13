from __future__ import annotations

from functools import lru_cache
from typing import *

from core.common import DynamicString, DynamicStyles, DynamicClasses, UniqueNode, typename
from core.components.htmlnode import HTMLTemplate
from core.components.loader import collect_template
from core.session import Session

if TYPE_CHECKING:
    from core.components.context import AnyNode, Context, HTMLElement, Condition, \
        TextNode, Slot

import logging

logger = logging.getLogger(__name__)


class RenderNode(UniqueNode):
    __slots__ = ['context', 'shot', 'session']

    def __init__(self, parent: Optional[RenderNode], render_this: bool = False, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        super().__init__(parent)
        self.shot: 'ContextShot' = shot or parent.shot
        self.session: Session = session or parent.session
        if render_this:
            self.shot(self)
        if typename(self) == 'Context':
            self.context = self
        else:
            self.context = parent.context

    def empty(self):
        for child in self.children:  # type: RenderNode
            self.shot -= child
            child.empty()
        self.children.clear()

    def remove(self, node=None):
        if node:
            super().remove(node)
        else:
            self.empty()
            self.shot -= self
            if self.parent:
                self.parent.remove(self)

    def update(self):
        self.context.render.update(self)

    def update_tree(self):
        self.context.render.update(self, True)

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return None

    def clone(self, new_parent: Optional[AnyNode] = None) -> Optional[HTMLElement, TextNode]:
        if new_parent is None:
            new_parent = self.context

        clone: Optional[AnyNode] = self._clone(new_parent)
        if clone:
            for child in self.children:
                sub = child.clone(clone)
                if sub:
                    clone.append(sub)
        return clone


@lru_cache(None, False)
def common_globals():
    globals = {}
    exec('from core.ctx import *', globals)
    return globals


class DefaultRenderer:
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

    def __call__(self, node: AnyNode, content: Union[str, AnyNode]):
        self.render(node, content)

    def build(self):
        self.build_node(self.ctx.template, self.ctx)

    def build_func(self, text: str, node: RenderNode) -> Callable[[], Any]:
        return lambda: eval(text, {'ctx': self.ctx, 'this': node}, self.ctx.locals)

    @staticmethod
    def strip_quotes(s):
        return s.strip('" ''')

    def build_string(self, source: str, node: RenderNode) -> Optional[Union[str, DynamicString]]:
        if not source:
            return None

        if '{' in source:
            return DynamicString(self.build_func('f'+source, node))
        else:
            return self.strip_quotes(source)

    def eval_string(self, source: str, node: RenderNode) -> Any:
        if not source:
            return None

        if '{' in source:
            return self.build_func(source.strip('" ''{}'), node)()
        else:
            return self.strip_quotes(source)

    def process_special_attribute(self, attr: str, value: str, node: Optional[HTMLElement] = None) -> bool:
        if attr.startswith('ref:'):
            name = attr.split(':')[1].strip()
            self.ctx.refs[name] = node
            return True
        elif attr.startswith('local:'):
            name = attr.split(':')[1].strip()
            node.context.locals[name] = self.eval_string(value, node)
            return True
        elif attr == 'on:render':
            value = self.strip_quotes(value)
            self.ctx[value](node)
            return True
        elif attr == 'style':
            if '{' in value:
                node.style = self.build_string(value, node)
            else:
                node.style = DynamicStyles(self.strip_quotes(value))
            return True
        return False

    def build_node(self, template: HTMLTemplate, parent: Optional[RenderNode]) -> Optional[RenderNode]:
        import core.components.context as c
        node: Optional[AnyNode] = None
        if template.tag_name[0] == '#':
            if template.tag_name == '#if':
                node = c.ConditionNode(parent)
                for child_template in template.children:  # type: HTMLTemplate
                    if child_template.tag_name != '#else':
                        item = c.Condition(self.build_func(child_template.macro, node), child_template)
                    else:
                        item = c.Condition((lambda: True), child_template)
                    node.conditions.append(item)
                self.update(node)

            elif template.tag_name == '#for':
                node = c.LoopNode(parent, template)
                chunks = template.macro.split(' in ')
                node.var_name = chunks[0].strip()
                node.iterator = self.build_func(chunks[1], node)
                self.update(node)

        elif template.tag_name[0].isupper():
            node_template = collect_template(self.ctx.session, template.tag_name)
            if not node_template: return None
            node = c.Context(node_template, parent)

            # attach slots
            if template.children:
                node.slot = c.Slot(self.ctx, template)

            # evaluate attributes
            for attr, value in template.attributes.items():
                if not self.process_special_attribute(attr, value, node):
                    node.locals[attr] = self.build_string(value, node)

            node.render.build()

        elif template.tag_name == 'slot':
            slot: Slot = parent.context.slot
            slot_template = None
            if slot:
                name = template.attributes.get('name')
                if name:
                    name = self.build_string(name, parent)
                    for child in slot.template.children:
                        if child.tag_name == name:
                            slot_template = child
                            break
                else:
                    slot_template = slot.template

            if not slot_template:
                for child in template.children:
                    self.build_node(child, parent)
            else:
                current_ctx = self.ctx
                self.ctx = slot.ctx
                for child in slot_template.children:
                    self.build_node(child, parent)
                self.ctx = current_ctx

        elif template.tag_name == 'python':
            if not self.ctx._executed:
                self.ctx._executed = True
                initial_locals = dict(self.ctx.locals)
                self.ctx.locals += {'ctx': self.ctx, 'refs': self.ctx.refs}
                try:
                    if not template.code:
                        template.code = compile(template.text, template.filename, 'exec')
                    # exec(template.code, common_globals(), self.ctx.locals)
                    exec(template.code, self.ctx.locals)
                    self.ctx.locals.update(initial_locals)
                    if 'init' in self.ctx.locals:
                        self.ctx.locals.init()
                    if 'ns_type' in self.ctx.locals:
                        self.ctx.ns_type = self.ctx.locals.ns_type
                except Exception as e:
                    logger.error(
                        f'{template.filename}:\n[{e.args[1][1]}:{e.args[1][2]}] {e.args[0]}\n{e.args[1][3]}{" " * e.args[1][2]}^')

        elif template.tag_name == 'style':
            # styles collected elsewhere
            if 'global' not in template.attributes:
                self.ctx.render_base = True

        elif template.tag_name == 'event':
            node = c.EventNode(parent)
            for k, v in template.attributes.items():
                if k == 'selector':
                    node.attributes[k] = ','.join(f'.ctx-{self.ctx.template.name} {s}' for s in self.strip_quotes(v).split(','))
                else:
                    node.attributes[k] = self.build_string(v, node)
            self.ctx.render_base = True

        elif template.tag_name == '@text':
            node = c.TextNode(parent, self.strip_quotes(template.text))

        elif template.tag_name[0] == '$':
            node = self.ctx
            node.context = node

            for child in template.children:
                self.build_node(child, node)

        else:
            # reconstruct HTML element

            node = c.HTMLElement(template.tag_name, parent=parent)
            # evaluate attributes
            for attr, value in template.attributes.items():
                if not self.process_special_attribute(attr, value, node):
                    node.attributes[attr] = self.build_string(value, node)

            node.classes = self.build_string(template.classes, node)
            if type(node.classes) == str:
                node.classes = DynamicClasses(node.classes)

            # evaluate body
            # element.text = self.build_string(template.text)

            # evaluate children
            if template.tag_name == 'macro':
                node.text = DynamicString(self.build_func(template.macro, node))
            elif len(template.children) == 1 and template.children[0].tag_name == '@text':
                node.text = template.children[0].text
            else:
                for child in template.children:
                    self.build_node(child, node)
        return node

    def update_children(self, node: AnyNode):
        for child in node.children:
            self.update(child, True)

    def update(self, node: AnyNode, recursive: bool = False):
        if typename(node) in ('HTMLElement', 'NSElement'):
            # attributes, classes and text evaluation
            for k, v in node.attributes.items():
                if type(v) == DynamicString:
                    node.attributes[k] = v()
            if type(node.classes) == DynamicString:
                node.classes = node.classes()
            elif type(node.classes) == str:
                node.classes = DynamicClasses(node.classes)
            if type(node.style) == DynamicString:
                node.style = node.style()
            if type(node.text) == DynamicString:
                node.text = node.text()
            node.shot(node)

        elif typename(node) == 'Context':
            if node.children:
                node.empty()
            self.build_node(node.template, node)
            return  # prevent repeated updates

        elif typename(node) == 'TextNode':
            if type(node.text) == DynamicString:
                node.text = node.text()
            node.shot(node)
            return  # no children ever

        elif typename(node) == 'ConditionNode':
            state: int = -1
            condition: Optional[Condition] = None
            for i, c in enumerate(node.conditions):
                if c.func():
                    state = i
                    condition = c
                    break

            if node.state != state:
                if node.state >= 0:
                    node.empty()
                if state == -1:
                    return

                for child in condition.template.children:
                    self.build_node(child, node)

                return  # prevent repeated updates

        elif typename(node) == 'LoopNode':
            node.empty()
            for value in node.iterator():
                self.ctx.locals[node.var_name] = value
                for temp_child in node.template.children:
                    self.build_node(temp_child, node)
            return  # prevent repeated updates

        if recursive:
            self.update_children(node)

    def render(self, node: AnyNode, content: Union[str, AnyNode]):
        if type(content) == str:
            node.text = content
            self.ctx.shot(node)
        else:
            content.parent = node
            self.update_children(node)


class ContextShot:
    __slots__ = ['updated', 'deleted']

    def __init__(self):
        self.updated: List[AnyNode] = list()
        self.deleted: Set[int] = set()

    def reset(self):
        self.updated.clear()
        self.deleted.clear()

    def __call__(self, node):
        self.updated.append(node)

    def __add__(self, other):
        self.updated.append(other)
        return self

    def __sub__(self, other):
        self.deleted.add(other.oid)
        return self

    @property
    def rendered(self) -> List[RenderNode]:
        from core.components.context import Context
        return [node for node in self.updated if type(node) != Context or node.render_base]
