from __future__ import annotations

import threading
from copy import deepcopy
from enum import Enum, auto
from typing import *
from dataclasses import dataclass

from attrdict import AttrDict

from .loader import collect_template
from ..common import DynamicStyles, EmptyCaller, DynamicClasses, MetricsData, WebUnits
from .htmlnode import HTMLTemplate

from .render import RenderNode, DefaultRenderer
from ..oid import get_node

if TYPE_CHECKING:
    from ..common import DynamicString
    from .render import ContextShot
    from ..session import Session


AnyNode = Union['Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode', 'EventNode']

class NSType(Enum):
    HTML = auto()       # http://www.w3.org/1999/xhtml
    SVG = auto()        # http://www.w3.org/2000/svg
    SVG_EV = auto()     # http://www.w3.org/2001/xml-events
    SVG_XLINK = auto()  # http://www.w3.org/1999/xlink
    MATH = auto()       # http://www.w3.org/1998/Math/MathML


class Slot(NamedTuple):
    ctx: 'Context'
    template: HTMLTemplate


class Context(RenderNode):
    __slots__ = ['locals', '_executed', 'refs', 'slot', 'template', 'render', 'render_base', 'ns_type']

    def __init__(self, template: Union[HTMLTemplate, str], parent: Optional[RenderNode] = None, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        self.locals: AttrDict = AttrDict()
        self._executed: bool = False
        self.refs: Dict[str, Union['Context', HTMLElement]] = AttrDict()
        self.slot: Optional[Slot] = None

        super().__init__(parent=parent, render_this=True, shot=shot, session=session)

        if type(template) == HTMLTemplate:
            self.template: HTMLTemplate = template
        else:
            self.template = collect_template(self.session, template)

        self.render: DefaultRenderer = DefaultRenderer(self)
        self.render_base = False
        self.ns_type: Optional[NSType] = parent and parent.context.ns_type

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement(self.template.name, new_parent)

    @property
    def tag_name(self):
        return self.template.name

    def __getitem__(self, item: str):
        if item in self.locals:
            return self.locals[item]
        return self.parent.context[item] if self.parent else EmptyCaller()

    def __setitem__(self, key, value):
        self.locals[key] = value

    def __str__(self):
        return f'Context: {self.template.name} {self.oid}'


class HTMLElement(RenderNode):
    __slots__ = ['tag_name', 'attributes', 'classes', 'text', 'style',
                 '_set_focus', '_metrics', '_metrics_ev', '_value', '_value_ev'
                 ]

    def __new__(cls, tag_name: str, parent: RenderNode, attributes: Optional[Union[Dict, AttrDict]] = None, text: str = ''):
        if parent and not parent.context.ns_type:
            return super().__new__(cls)
        instance = super().__new__(NSElement)
        instance.ns_type = parent.context.ns_type
        return instance

    def __init__(self, tag_name: str, parent: RenderNode, attributes: Optional[Union[Dict, AttrDict]] = None, text: str = ''):
        super().__init__(parent, True)
        self.tag_name: str = tag_name
        self.attributes: AttrDict = attributes and AttrDict(attributes) or AttrDict()
        self.classes: Optional[Union[DynamicClasses, DynamicString, str]] = DynamicClasses()
        self.style: Union[DynamicStyles, DynamicString, str] = DynamicStyles()
        self.text: Union[DynamicString, str] = text
        self._set_focus = False

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        clone: HTMLElement = HTMLElement(self.tag_name, new_parent)
        clone.attributes = AttrDict({
            k: v
            for k, v in self.attributes.items() if k[:3] != 'on:' and not k.startswith('ref:')
        })
        clone.text = self.text
        clone.classes = deepcopy(self.classes)
        clone.style = deepcopy(self.style)
        return clone

    def render(self, content: Union[str, RenderNode]):
        self.context.render(self, content)

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
        self._metrics_cv.wait()

    @property
    def metrics(self):
        if hasattr(self, '_metrics'):
            return self._metrics
        self.request_metrics()
        return self._metrics

    def set_metrics(self, m: Union[MetricsData, Dict[str, Union[int, str]], List[Union[int, str]]], shift: int = 0, grow: int = 0):
        if isinstance(m, dict):
            m = AttrDict(m)
        elif isinstance(m, list):
            m = AttrDict({k: v for k, v in zip(['left', 'top', 'width', 'height'], m)})
        self.style.position = 'fixed'
        self.style.left = WebUnits(m.left) + shift
        self.style.top = WebUnits(m.top) + shift
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
        self.session.request_value(self)
        self._value_ev.wait()
        return self._value

    def move(self, delta_x, delta_y):
        self.style.left += delta_x
        self.style.top += delta_y
        self.shot(self)

    def focus(self):
        self._set_focus = True

    def __getitem__(self, item: str):
        return self.context[item]

    def __str__(self):
        return f'HTML: {self.tag_name} {self.oid}'


class NSElement(HTMLElement):
    __slots__ = ['ns_type']

    def __str__(self):
        return f'{NSType(self.ns_type).name}: {self.tag_name} {self.oid}'


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

    @property
    def tag_name(self):
        return 'condition'

    def __str__(self):
        return f'Condition {self.oid}'


class LoopNode(RenderNode):
    __slots__ = ['template', 'var_name', 'iterator']

    def __init__(self, parent: RenderNode, template: HTMLTemplate):
        super().__init__(parent, False)

        self.template: Optional[HTMLTemplate] = template
        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement('loop', new_parent)

    @property
    def tag_name(self):
        return 'loop'

    def __str__(self):
        return f'Loop {self.oid}'


class TextNode(RenderNode):
    __slots__ = ['text']

    def __init__(self, parent: RenderNode, text: str):
        super().__init__(parent, True)
        self.text: str = text

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return TextNode(new_parent, self.text)

    @property
    def tag_name(self):
        return 'text'

    def __str__(self):
        return f'Text {self.oid}'


class EventNode(RenderNode):
    __slots__ = ['attributes']

    def __init__(self, parent: RenderNode, attributes: Optional[AttrDict] = None):
        super().__init__(parent, True)
        self.attributes = attributes or AttrDict()

