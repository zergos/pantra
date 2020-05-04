from __future__ import annotations

import threading
from contextlib import contextmanager
from copy import deepcopy
from typing import *

from attrdict import AttrDict

from core.common import DynamicString, DynamicStyles, DynamicClasses, MetricsData, Pixels
from core.components.htmlnode import HTMLTemplate, collect_template
from core.oid import get_node
from core.session import Session

if TYPE_CHECKING:
    from core.components.context import Context, AnyNode, HTMLElement, ConditionNode, Condition, LoopNode, SlotNode, \
        TextNode

import logging

logger = logging.getLogger(__name__)


class RenderMixin:
    #__slots__ = ['context', 'shot']

    def __init__(self, parent: Optional[AnyNode], **kwargs):
        from core.components.context import Context
        self.shot: 'ContextShot' = kwargs.get('shot') or parent.shot
        self.session: Session = kwargs.get('session') or parent.session
        self.shot(self)
        if type(self) == Context:
            self.context = self
        else:
            self.context = kwargs.get('context') or parent.context
        self._set_focus = False

    def empty(self):
        for child in self._NodeMixin__children_:  # type: AnyNode
            self.shot -= child
            child.empty()
        self._NodeMixin__children_.clear()

    def remove(self):
        self.empty()
        self.shot -= self
        if hasattr(self, '_NodeMixin__parent'):
            self._NodeMixin__parent._NodeMixin__children.remove(self)

    def update(self):
        self.context.render.update(self)

    def update_tree(self):
        self.context.render.update(self, True)

    @staticmethod
    def _set_metrics(oid: int, metrics: Dict[str, int]):
        self = get_node(oid)
        if self is None: return
        self._metrics = MetricsData(metrics['x'], metrics['y'], metrics['x']+metrics['w'], metrics['y']+metrics['h'], metrics['w'], metrics['h'])
        self.session.metrics_stack.append(self)
        with self._metrics_cv:
            self._metrics_cv.notify()

    def request_metrics(self):
        if not hasattr(self, '_metrics_cv'):
            self._metrics_cv = threading.Condition()
        with self._metrics_cv:
            self.session.request_metrics(self)
            self._metrics_cv.wait()

    @property
    def metrics(self):
        if hasattr(self, '_metrics'):
            return self._metrics
        self.request_metrics()
        return self._metrics

    def set_metrics(self, m: Union[MetricsData, Dict[str, int], List[int]], shrink: int = 0):
        if isinstance(m, dict):
            m = AttrDict(m)
        elif isinstance(m, list):
            m = AttrDict({k: v for k, v in zip(['left', 'top', 'width', 'height'], m)})
        self.style.position = 'fixed'
        self.style.left = Pixels(m.left)
        self.style.top = Pixels(m.top)
        self.style.width = Pixels(m.width) - shrink
        self.style.height = Pixels(m.height) - shrink
        self.shot(self)

    @staticmethod
    def _set_value(oid: int, value):
        self = get_node(oid)
        if self is None: return
        self._value = value
        with self._value_cv:
            self._value_cv.notify()

    @property
    def value(self):
        if not hasattr(self, '_value_cv'):
            self._value_cv = threading.Condition()
        with self._value_cv:
            self.session.request_value(self)
            self._value_cv.wait()
        return self._value

    def move(self, delta_x, delta_y):
        self.style.left += delta_x
        self.style.top += delta_y
        self.shot(self)

    def clone(self, new_parent: Optional[AnyNode] = None) -> HTMLElement:
        from core.components.context import Context, HTMLElement, ConditionNode, LoopNode, TextNode
        if new_parent is None:
            new_parent = self.context
        clone: Optional[AnyNode] = None
        if type(self) == HTMLElement:
            clone: HTMLElement = HTMLElement(self.tag_name, new_parent, shot=self.shot, session=self.session, context=self.context)
            clone.attributes = AttrDict({
                k: v
                for k, v in self.attributes.items() if k[:3] != 'on:' and not k.startswith('ref:')
            })
            clone.text = self.text
            clone.classes = deepcopy(self.classes)
            clone.style = deepcopy(self.style)
        elif type(self) == Context:
            clone = HTMLElement(self.template.name, new_parent)
        elif type(self) == LoopNode:
            clone = HTMLElement('loop', new_parent)
        elif type(self) == ConditionNode:
            clone = HTMLElement('condition', new_parent)
        elif type(self) == TextNode:
            clone: TextNode = TextNode(new_parent, self.text)

        for child in self.children:
            clone.append(child.clone(clone))
        return clone

    def focus(self):
        self._set_focus = True


class DefaultRenderer:
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def __call__(self, node: AnyNode, content: Union[str, AnyNode]):
        self.render(node, content)

    def build(self):
        self.build_node(self.ctx.template, self.ctx, True)

    def build_func(self, text: str, node: AnyNode) -> Callable[[], Any]:
        return lambda: eval(text, {'ctx': self.ctx, 'this': node}, self.ctx.locals)

    def build_string(self, source: str, node: AnyNode) -> Optional[Union[str, DynamicString]]:
        if not source:
            return None

        if '{' in source:
            return DynamicString(self.build_func('f'+source, node))
        else:
            return source.strip('"'' ')

    def process_special_attribute(self, attr: str, value: str, node: Optional[HTMLElement] = None) -> bool:
        if attr.startswith('ref:'):
            name = attr.split(':')[1].strip()
            self.ctx.refs[name] = node
            return True
        elif attr == 'style':
            if '{' in value:
                node.style = self.build_string(value, node)
            else:
                node.style = DynamicStyles(value.strip('" '''))
            return True
        return False

    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode], is_root_node: bool = False) -> Optional[AnyNode]:
        from core.components.context import Context, SlotNode, ConditionNode, Condition, HTMLElement, LoopNode, EventNode
        node: Optional[AnyNode] = None
        if template.tag_name[0] == '#':
            if template.tag_name == '#if':
                node = ConditionNode(parent)
                for child_template in template.children:  # type: HTMLTemplate
                    if child_template.tag_name != '#else':
                        item = Condition(self.build_func(child_template.macro, node), child_template, None)
                    else:
                        item = Condition((lambda: True), child_template, None)
                    node.conditions.append(item)
                self.update(node)

            elif template.tag_name == '#for':
                node = LoopNode(parent=parent, template=template)
                chunks = template.macro.split(' in ')
                node.var_name = chunks[0].strip()
                node.iterator = self.build_func(chunks[1], node)
                self.update(node)

        elif template.tag_name[0].isupper():
            node_template = collect_template(template.tag_name)
            node = Context(template=node_template, parent=parent)

            # evaluate slot
            if template.children:
                with node.shot.freeze():
                    node.slot = SlotNode(parent=parent)
                    for child in template.children:
                        self.build_node(child, node.slot)

            # evaluate attributes
            for attr, value in template.attributes.items():
                if not self.process_special_attribute(attr, value, node):
                    node.locals[attr] = self.build_string(value, node)

            node.render.build()

        elif template.tag_name == 'slot':
            if parent.context.slot:
                for child in parent.context.slot.children:
                    parent.append(child)
                    self.ctx.shot(child)
            else:
                for child in template.children:
                    self.build_node(child, parent)

        elif template.tag_name == 'python':
            saved = dict(self.ctx.locals)
            self.ctx.locals += {'ctx': self.ctx, 'refs': self.ctx.refs}
            try:
                if not template.code:
                    template.code = compile(template.text, template.filename, 'exec')
                exec(template.code, self.ctx.locals)
            except Exception as e:
                logger.error(
                    f'{template.filename}:\n[{e.args[1][1]}:{e.args[1][2]}] {e.args[0]}\n{e.args[1][3]}{" " * e.args[1][2]}^')
            else:
                self.ctx.locals.update(saved)
                if 'init' in self.ctx.locals:
                    self.ctx.locals.init()

        elif template.tag_name == 'style':
            # styles collected elsewhere
            pass

        elif template.tag_name == 'event':
            node = EventNode(parent)
            for k, v in template.attributes.items():
                if k == 'selector':
                    node.attributes[k] = ','.join(f'.default .ctx-{self.ctx.template.name} {s}' for s in v.strip('" ''').split(','))
                else:
                    node.attributes[k] = self.build_string(v, node)

        elif template.tag_name == '@text':
            node = TextNode(parent=parent, text=template.text.strip('"'' '))

        else:
            # reconstruct HTML element

            if is_root_node:
                node = self.ctx
                node.context = node

            else:
                node = HTMLElement(template.tag_name, parent=parent)
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
        from core.components.context import HTMLElement, Context, TextNode, ConditionNode, LoopNode
        if type(node) == HTMLElement:
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

        elif type(node) == Context:
            if node.children:
                node.empty()
            node.shot(node)
            self.build_node(node.template, node, True)
            return  # prevent repeated updates

        elif type(node) == TextNode:
            if type(node.text) == DynamicString:
                node.text = node.text()
            node.shot(node)
            return  # no children ever

        elif type(node) == ConditionNode:
            state: int = -1
            condition: Optional[Condition] = None
            for i, c in enumerate(node.conditions):
                if c.func():
                    state = i
                    condition = c
                    break

            if node.state != state:
                node.empty()
                node.shot(node)
                if state == -1:
                    return

                sub_node = condition.node
                if not sub_node:
                    sub_node = self.build_node(condition.template, node)
                    node.conditions[state].node = sub_node
                else:
                    sub_node.parent = node
                    self.update_children(sub_node)

                return  # prevent repeated updates

        elif type(node) == LoopNode:
            node.empty()
            node.shot(node)
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
    __slots__ = ['updated', 'deleted', 'frozen']

    def __init__(self):
        self.updated: List[AnyNode] = list()
        self.deleted: Set[int] = set()
        self.frozen: bool = False

    def reset(self):
        self.updated = list()
        self.deleted = set()

    @contextmanager
    def freeze(self):
        self.frozen = True
        yield
        self.frozen = False

    def __call__(self, node):
        if not self.frozen:
            self.updated.append(node)

    def __add__(self, other):
        if not self.frozen:
            self.updated.append(other)
        return self

    def __sub__(self, other):
        self.deleted.add(other.oid)
        return self
