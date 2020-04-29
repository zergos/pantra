import os
import threading
import uuid
from contextlib import contextmanager
from copy import deepcopy
from typing import *
import re
from dataclasses import dataclass, field
import ctypes

from attrdict import AttrDict
from anytree import NodeMixin

from core.common import UniNode, DynamicString, DynamicClasses, DynamicStyles, MetricsData
from .htmlnode import HTMLNode, HTMLTemplate, collect_template

from logging import getLogger

from ..oid import gen_id, get_object
from ..session import Session
from ..workers import thread_worker

logger = getLogger(__name__)

AnyNode = Union['HTMLElement', 'Context', 'ConditionNode', 'LoopNode', 'SlotNode', 'TextNode']


class RenderMixin:
    #__slots__ = ['context', 'shot']

    def __init__(self, node: AnyNode, shot: Optional['ContextShot'] = None, session: Optional[Session] = None):
        self.shot: 'ContextShot' = shot or node.shot
        self.session: Session = session or node.session
        self.shot(self)
        if type(self) == Context:
            self.context = self
        else:
            self.context = node.context

    def empty(self):
        for child in self._NodeMixin__children_:  # type: AnyNode
            self.shot -= child
            child.empty()
        self._NodeMixin__children_.clear()

    def remove(self):
        self.empty()
        self.shot -= self
        self.parent.remove(self)

    def update(self):
        self.context.render.update(self)

    def update_tree(self):
        self.context.render.update(self, True)

    @staticmethod
    def _set_metrics(oid: int, metrics: Dict[str, int]):
        self = get_object(oid)
        self._metrics = MetricsData(metrics['x'], metrics['y'], metrics['x']+metrics['w'], metrics['y']+metrics['h'], metrics['w'], metrics['h'])
        with self._metrics_cv:
            self._metrics_cv.notify()

    def request_metrics(self):
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

    def set_metrics(self, m: MetricsData):
        self.attributes.position = 'fixed'
        self.attributes.left = m.left
        self.attributes.top = m.top
        self.attributes.width = m.width
        self.attributes.height = m.height
        self.shot += self

    def move(self, delta_x, delta_y):
        self.attributes.left += delta_x
        self.attributes.top += delta_y
        self.shot += self


class Context(UniNode, RenderMixin):
    __slots__ = ['locals', 'server_events', 'refs', 'slot', 'template', 'render']

    def __init__(self, template: Union[HTMLTemplate, str], parent: Optional[AnyNode] = None, shot: Optional['ContextShot'] = None, session: Optional[Session] = None):
        #self.uid = uuid.UUID()
        self.locals = AttrDict()
        self.server_events = AttrDict()
        self.refs: Dict[str, Union['Context', HTMLElement]] = AttrDict()
        self.slot: Optional['SlotNode'] = None
        if type(template) == HTMLTemplate:
            self.template: HTMLTemplate = template
        else:
            self.template = collect_template(template)

        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent, shot, session)
        self.render: DefaultRenderer = DefaultRenderer(self)

    def __getitem__(self, item: str):
        if item in self.locals:
            return self.locals[item]
        result = self.parent[item] if self.parent else ''
        return result

    def __setitem__(self, key, value):
        if key in self.locals:
            self.locals[key] = value

    def __str__(self):
        return f'Context: {self.template.name}'


class HTMLElement(HTMLNode, RenderMixin):
    __slots__ = ['text', 'style']

    def __init__(self, tag_name: str, parent: AnyNode, attributes: Optional[Union[Dict, AttrDict]] = None):
        super().__init__(tag_name=tag_name, parent=parent, attributes=attributes)
        RenderMixin.__init__(self, parent)
        self.style: Optional[Union[DynamicStyles, DynamicString, str]] = None
        self.text: Union[str, DynamicString] = ''

    def render(self, content: Union[str, AnyNode]):
        self.context.render(self, content)

    def clone(self, new_parent: Optional[AnyNode] = None) -> 'HTMLElement':
        clone: HTMLElement = HTMLElement(self.tag_name, new_parent, AttrDict(self.attributes))
        clone.shot = self.shot
        clone.text = self.text
        clone.classes = deepcopy(self.classes)
        clone.style = deepcopy(self.style)
        self.shot += clone
        return clone

    def __str__(self):
        return f'HTML: {self.tag_name}'


@dataclass
class Condition:
    __slots__ = ['func', 'template', 'node']
    func: Callable[[], bool]
    template: HTMLTemplate
    node: Optional[AnyNode]


class ConditionNode(UniNode, RenderMixin):
    __slots__ = ['state', 'conditions']

    def __init__(self, parent: AnyNode):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)
        self.state = -1
        self.conditions: Optional[List[Condition]] = []


class LoopNode(UniNode, RenderMixin):
    __slots__ = ['template', 'var_name', 'iterator']

    def __init__(self, parent: AnyNode, template: HTMLTemplate):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)

        self.template: Optional[HTMLTemplate] = template
        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None


class SlotNode(UniNode, RenderMixin):
    def __init__(self, parent: AnyNode):
        super().__init__()
        RenderMixin.__init__(self, parent)


class TextNode(UniNode, RenderMixin):
    __slots__ = ['text']

    def __init__(self, parent: AnyNode, text: str):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)
        self.text: str = text


# **** Render block ****

class DefaultRenderer:
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def __call__(self, node: AnyNode, content: Union[str, AnyNode]):
        self.render(node, content)

    def build(self):
        self.build_node(self.ctx.template, self.ctx, True)

    def build_func(self, text: str) -> Callable[[], Any]:
        return lambda: eval(text, {'ctx': self.ctx}, self.ctx.locals)

    def build_string(self, source: str) -> Optional[Union[str, DynamicString]]:
        if not source:
            return None

        if '{' in source:
            return DynamicString(self.build_func('f'+source))
        else:
            return source.strip('"'' ')

    def process_special_attribute(self, attr: str, value: str, node: Optional[HTMLElement] = None) -> bool:
        if attr.startswith('ref:'):
            name = attr.split(':')[1].strip()
            self.ctx.refs[name] = node
            return True
        elif attr == 'style':
            if '{' in value:
                node.style = self.build_string(value)
            else:
                node.style = DynamicStyles(value.strip('" '''))
            return True
        return False

    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode], is_root_node: bool = False) -> Optional[AnyNode]:
        node: Optional[AnyNode] = None
        if template.tag_name[0] == '#':
            if template.tag_name == '#if':
                node = ConditionNode(parent)
                for child_template in template.children:  # type: HTMLTemplate
                    if child_template.tag_name != '#else':
                        item = Condition(self.build_func(child_template.macro), child_template, None)
                    else:
                        item = Condition((lambda: True), child_template, None)
                    node.conditions.append(item)
                self.update(node)

            elif template.tag_name == '#for':
                node = LoopNode(parent=parent, template=template)
                chunks = template.macro.split(' in ')
                node.var_name = chunks[0].strip()
                node.iterator = self.build_func(chunks[1])
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
                    node.locals[attr] = self.build_string(value)

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
            self.ctx.locals += {'ctx': self.ctx, 'refs': self.ctx.refs}
            try:
                if not template.code:
                    template.code = compile(template.text, template.filename, 'exec')
                exec(template.code, self.ctx.locals)
            except Exception as e:
                logger.error(
                    f'{template.filename}:\n[{e.args[1][1]}:{e.args[1][2]}] {e.args[0]}\n{e.args[1][3]}{" " * e.args[1][2]}^')
            if 'init' in self.ctx.locals:
                self.ctx.locals.init()

        elif template.tag_name == 'style':
            # styles collected elsewhere
            pass

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
                        node.attributes[attr] = self.build_string(value)

            node.classes = self.build_string(template.classes)
            if type(node.classes) == str:
                node.classes = DynamicClasses(node.classes)

            # evaluate body
            # element.text = self.build_string(template.text)

            # evaluate children
            if template.tag_name == 'macro':
                node.text = DynamicString(self.build_func(template.macro))
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

    def __call__(self, node: AnyNode, *args, **kwargs):
        if not self.frozen:
            self.updated.append(node)

    def __add__(self, other):
        if not self.frozen:
            self.updated.append(other)

    def __sub__(self, other):
        self.deleted.add(gen_id(other))
        return self

