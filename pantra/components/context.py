from __future__ import annotations

import typing
import threading
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum, auto
from dataclasses import dataclass

from pantra.common import ADict

from .loader import collect_template, HTMLTemplate
from pantra.common import DynamicStyles, EmptyCaller, DynamicClasses, WebUnits

from pantra.components.render import RenderNode, DefaultRenderer
from pantra.components.watchdict import WatchDict, WatchDictActive
from pantra.oid import get_node
from pantra.defaults import *

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.common import DynamicString
    from pantra.components.render import ContextShot
    from pantra.session import Session

__all__ = ['NSType', 'HTMLTemplate', 'Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode',
           'EventNode', 'SetNode', 'ReactNode', 'ScriptNode', 'AnyNode']

AnyNode = typing.Union['Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode', 'EventNode',
            'SetNode', 'ReactNode', 'ScriptNode']


class NSType(Enum):
    HTML = auto()       # http://www.w3.org/1999/xhtml
    SVG = auto()        # http://www.w3.org/2000/svg
    SVG_EV = auto()     # http://www.w3.org/2001/xml-events
    SVG_XLINK = auto()  # http://www.w3.org/1999/xlink
    MATH = auto()       # http://www.w3.org/1998/Math/MathML
    FB = auto()         # http://www.facebook.com/2008/fbml


@dataclass
class MetricsData:
    __slots__ = ['left', 'top', 'right', 'bottom', 'width', 'height']
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int


class Slot(typing.NamedTuple):
    ctx: Context
    template: HTMLTemplate

    def __getitem__(self, name: Union[str, int]) -> Union[Context, HTMLTemplate, Slot, None]:
        if type(name) == str:
            for child in self.template.children:
                if child.tag_name == name:
                    if 'reuse' in child.attributes:
                        return self.ctx.slot[name] if self.ctx.slot else None
                    else:
                        return Slot(self.ctx, child)
        else:
            raise NotImplementedError('integer indexing')  # return super().__getitem__(name)


class Context(RenderNode):
    __slots__ = ['locals', '_executed', 'refs', 'slot', 'template', 'render', '_restyle', 'ns_type', 'react_vars',
                 'react_nodes', 'source_attributes', 'allowed_call']

    def __init__(self, template: Union[HTMLTemplate, str], parent: Optional[RenderNode] = None, shot: Optional[ContextShot] = None, session: Optional[Session] = None, locals: Optional[Dict] = None):
        self.locals: WatchDict = WatchDict(self)
        if locals:
            self.locals.update(locals)
        self._executed: bool = False
        self.refs: Dict[str, Union['Context', HTMLElement, WatchDict]] = ADict()
        self.slot: Optional[Slot] = None
        self.source_attributes: Optional[Dict[str, Any]] = None
        self.allowed_call: set[str] = set()

        super().__init__(parent=parent, render_this=False, shot=shot, session=session)

        if type(template) == HTMLTemplate:
            self.template: HTMLTemplate = template
        else:
            self.template: HTMLTemplate = collect_template(self.session, template)
            if not self.template:
                self.session.error(f'template {template} not found')
                raise NameError

        self.render: DefaultRenderer = DefaultRenderer(self)
        self._restyle: bool = False
        self.ns_type: Optional[NSType] = parent and parent.context.ns_type

        self.react_vars: Dict[str, Set[AnyNode]] = defaultdict(set)
        self.react_nodes: Set[AnyNode] = set()

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement(self.template.name, new_parent)

    def div(self, classes: str = '', src: Optional[HTMLElement] = None, from_x: int = 0, from_y: int = 0, attributes: Optional[Dict, None] = None):
        node = HTMLElement('div', self, attributes)
        node.classes = DynamicClasses(classes)
        if src:
            node.set_metrics(src.metrics, from_x=from_x, from_y=from_y)
        return node

    @contextmanager
    def record_reactions(self, node: AnyNode):
        self.locals.__class__ = WatchDictActive
        self.locals.start_record(node)
        yield
        self.locals.stop_record()
        self.locals.__class__ = WatchDict

    def call(self, action: str, *args, **kwargs):
        if action not in self.locals:
            return
        method = self.locals[action]
        if type(method) is str:
            if self.parent:
                self.parent.call(action, *args, **kwargs)
        else:
            method(*args, **kwargs)

    def __getitem__(self, item: Union[str, int]):
        if type(item) is int:
            return self.children[item]
        return self.locals.get(item, EmptyCaller())

    def __setitem__(self, key, value):
        setattr(self.locals, key, value)

    def set_quietly(self, key, value):
        self.locals[key] = value

    def __str__(self):
        return f'${self.template.name}' + (f':{self.name}' if self.name else '')

    def allow_call(self, method: str):
        self.allowed_call.add(method)

    def is_call_allowed(self, method: str) -> bool:
        return method in self.allowed_call or '*' in self.allowed_call


class ConditionalClass(typing.NamedTuple):
    condition: Callable[[], bool]
    cls: str


class ConditionalClasses(list):
    __slots__ = ['cache']

    def __init__(self, *args):
        super().__init__(*args)
        self.cache = ''

    def __call__(self):
        if not self:
            return ''
        res = []
        for check in self:
            if check[0]():
                res.append(check[1])
        self.cache = ' '.join(res)
        return self.cache


class HTMLElement(RenderNode):
    __slots__ = ['tag_name', 'attributes', 'classes', 'con_classes', 'text', 'style', 'data',
                 '_set_focus', '_metrics', '_metrics_ev', 'value_type', '_value', '_value_ev', '_validity', '_validity_ev'
                 ]

    def __new__(cls, tag_name: str, parent: AnyNode, attributes: Optional[Union[Dict, ADict]] = None, text: str = ''):
        if parent:
            if type(parent) is NSElement or type(parent) is Context and parent.ns_type:
                instance = super().__new__(NSElement)
                instance.ns_type = parent.ns_type
            elif parent.context.ns_type:
                instance = super().__new__(NSElement)
                instance.ns_type = parent.context.ns_type
            else:
                instance = super().__new__(cls)
        else:
            instance = super().__new__(cls)
        return instance

    def __init__(self, tag_name: str, parent: RenderNode, attributes: Optional[Union[Dict, ADict]] = None, text: str = ''):
        super().__init__(parent, True)
        self.tag_name: str = tag_name
        self.attributes: ADict[str, Any] = attributes and ADict(attributes) or ADict()
        self.classes: Union[DynamicClasses, DynamicString, str] = DynamicClasses()
        self.con_classes: ConditionalClasses = ConditionalClasses()
        self.style: Union[DynamicStyles, DynamicString, str] = DynamicStyles()
        self.text: Union[DynamicString, str] = text
        self.data: ADict[str, Any] = ADict()
        self._set_focus = False
        self.value_type = None

    @classmethod
    def parse(cls, element: str, parent: RenderNode, text: str = '') -> Optional[HTMLElement]:
        chunks = element.split(' ')
        if not chunks:
            return None
        tag_name = chunks[0]
        attributes = {}
        for chunk in chunks[1:]:
            if not chunk: continue
            sides = chunk.split('=')
            if len(sides) == 1:
                attributes[sides[0]] = None
            else:
                attributes[sides[0]] = sides[1].strip('" \'')
        return HTMLElement(tag_name, parent, attributes, text)

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        clone: HTMLElement = HTMLElement(self.tag_name, new_parent)
        clone.attributes = ADict({
            k: v
            for k, v in self.attributes.items() if k[:3] != 'on:' and not k.startswith('ref:')
        })
        clone.text = self.text
        clone.classes = deepcopy(self.classes)
        clone.style = deepcopy(self.style)
        return clone

    def render(self, template: Union[str, HTMLTemplate], locals: Dict = None, build: bool = True):
        self.context.render(template, self, locals, build)

    @staticmethod
    def _set_metrics(oid: int, metrics: Dict[str, int]):
        self = get_node(oid)
        if self is None: return
        self._metrics = MetricsData(metrics['x'], metrics['y'], metrics['x']+metrics['w'], metrics['y']+metrics['h'], metrics['w'], metrics['h'])
        self.session.metrics_stack.append(self)
        self._metrics_ev.set()

    def request_metrics(self):
        if not hasattr(self, '_metrics_cv'):
            self._metrics_ev = threading.Event()
        self.session.request_metrics(self)
        self._metrics_ev.wait(LOCKS_TIMEOUT)

    @property
    def metrics(self):
        if hasattr(self, '_metrics'):
            return self._metrics
        self.request_metrics()
        return self._metrics

    def set_metrics(self, m: Union[MetricsData, Dict[str, Union[int, str]], List[Union[int, str]]],
                    from_x: int = 0, from_y: int = 0, shift_x: int = 0, shift_y: int = 0, grow: int = 0):
        if isinstance(m, dict):
            m = ADict(m)
        elif isinstance(m, list):
            m = ADict({k: v for k, v in zip(['left', 'top', 'width', 'height'], m)})
        self.style.position = 'fixed'
        if from_x:
            m.left = from_x
        self.style.left = WebUnits(m.left) + shift_x
        if from_y:
            m.top = from_y
        self.style.top = WebUnits(m.top) + shift_y
        self.style.width = WebUnits(m.width) + grow
        self.style.height = WebUnits(m.height) + grow
        self.shot(self)

    @staticmethod
    def _set_value(oid: int, value):
        self = get_node(oid)
        if self is None: return
        self._value = value
        self._value_ev.set()

    @property
    def value(self):
        if hasattr(self, '_value'):
            return self._value
        if not hasattr(self, '_value_cv'):
            self._value_ev = threading.Event()
        self.session.request_value(self, self.value_type or 'text')
        self._value_ev.wait(LOCKS_TIMEOUT)
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def check_validity(self):
        if not hasattr(self, '_validity_ev'):
            self._validity_ev = threading.Event()
        self.session.request_validity(self)
        self._validity_ev.wait(LOCKS_TIMEOUT)
        return self._validity

    @staticmethod
    def _set_validity(oid: int, validity: bool):
        self = get_node(oid)
        if self is None: return
        self._validity = validity
        self._validity_ev.set()

    def move(self, delta_x, delta_y):
        self.style.left += delta_x
        self.style.top += delta_y
        self.shot(self)

    def set_focus(self):
        self._set_focus = True

    def add_class(self, class_name):
        self.classes += class_name
        self.shot(self)

    def remove_class(self, class_name):
        self.classes -= class_name
        self.shot(self)

    def toggle_class(self, class_name):
        self.classes *= class_name
        self.shot(self)

    def set_text(self, text: str):
        self.text = text
        self.shot(self)

    def __getitem__(self, item: Union[str, int]):
        if type(item) == int:
            return self.children[item]
        return self.context[item]

    def __setitem__(self, key, value):
        self.context[key] = value

    def set_quietly(self, key, value):
        self.context.set_quietly(key, value)

    def __str__(self):
        return self.tag_name + (f':{self.name}' if self.name else '')


class NSElement(HTMLElement):
    __slots__ = ['ns_type']

    def __str__(self):
        return f'{NSType(self.ns_type).name}:{self.tag_name}' + (f':{self.name}' if self.name else '')


@dataclass
class Condition:
    __slots__ = ['func', 'template']
    func: Callable[[], bool]
    template: HTMLTemplate


class ConditionNode(RenderNode):
    __slots__ = ['state', 'conditions']

    def __init__(self, parent: RenderNode):
        super().__init__(parent, False)
        self.state = -1
        self.conditions: Optional[List[Condition]] = []

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement('condition', new_parent)

    def __str__(self):
        return '?'


class LoopNode(RenderNode):
    __slots__ = ['template', 'else_template', 'var_name', 'iterator', 'index_func', 'index_map']

    def __init__(self, parent: RenderNode, template: HTMLTemplate):
        super().__init__(parent, False)

        self.template: Optional[HTMLTemplate] = template
        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None
        self.else_template: Optional[HTMLTemplate] = None
        self.index_func: Optional[Callable[[], Any]] = None
        self.index_map: Dict[Hashable, List[AnyNode]] = {}

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement('loop', new_parent)

    def reset_cache(self):
        self.index_map = {}

    def __str__(self):
        return '@'


class TextNode(RenderNode):
    __slots__ = ['text']

    def __init__(self, parent: RenderNode, text: Union[DynamicString, str]):
        super().__init__(parent, True)
        self.text: Union[DynamicString, str] = text

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return TextNode(new_parent, self.text)

    def __str__(self):
        return f'text'


class EventNode(RenderNode):
    __slots__ = ['attributes']

    def __init__(self, parent: RenderNode, attributes: Optional[ADict] = None):
        super().__init__(parent, True)
        self.attributes = attributes or ADict()


class SetNode(RenderNode):
    __slots__ = ['var_name', 'expr', 'template']

    def __init__(self, parent: RenderNode, template: HTMLTemplate):
        super().__init__(parent, False)
        self.template = template
        self.var_name = ''
        self.expr = ''

    def __str__(self):
        return ':='


class ReactNode(RenderNode):
    __slots__ = ['var_name', 'action', 'value']

    def __init__(self, parent: RenderNode, var_name: str, action: str):
        super().__init__(parent, False)
        self.var_name = var_name
        self.action = action
        self.value = None

    def __str__(self):
        return '>'


class ScriptNode(RenderNode):
    __slots__ = ['uid', 'attributes', 'text']

    def __init__(self, parent: RenderNode, uid: str, attributes: Optional[Union[Dict, ADict]] = None, text: str = ''):
        super().__init__(parent, True)
        self.attributes: ADict[str, Any] = attributes and ADict(attributes) or ADict()
        self.text: Union[DynamicString, str] = text
        self.uid: str = uid

    def __str__(self):
        return 'script'
