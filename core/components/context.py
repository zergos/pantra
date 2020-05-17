from __future__ import annotations

import typing
import threading
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum, auto
from dataclasses import dataclass

from common import UniNode
from core.common import ADict, HookDict

from .loader import collect_template
from core.common import DynamicStyles, EmptyCaller, DynamicClasses, MetricsData, WebUnits
from core.components.htmlnode import HTMLTemplate

from core.components.render import RenderNode, DefaultRenderer
from core.oid import get_node

if typing.TYPE_CHECKING:
    from typing import *
    from ..common import DynamicString
    from .render import ContextShot
    from ..session import Session

__all__ = ['NSType', 'Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode', 'EventNode', 'AnyNode']

AnyNode = typing.Union['Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode', 'EventNode']


class NSType(Enum):
    HTML = auto()       # http://www.w3.org/1999/xhtml
    SVG = auto()        # http://www.w3.org/2000/svg
    SVG_EV = auto()     # http://www.w3.org/2001/xml-events
    SVG_XLINK = auto()  # http://www.w3.org/1999/xlink
    MATH = auto()       # http://www.w3.org/1998/Math/MathML


class Slot(typing.NamedTuple):
    ctx: 'Context'
    template: HTMLTemplate


class Context(RenderNode):
    __slots__ = ['locals', '_executed', 'refs', 'slot', 'template', 'render', 'render_base', 'ns_type', 'react_vars', 'react_nodes']

    def __init__(self, template: Union[HTMLTemplate, str], parent: Optional[RenderNode] = None, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        self.locals: HookDict = HookDict()
        self._executed: bool = False
        self.refs: Dict[str, Union['Context', HTMLElement]] = ADict()
        self.slot: Optional[Slot] = None

        super().__init__(parent=parent, render_this=True, shot=shot, session=session)

        if type(template) == HTMLTemplate:
            self.template: HTMLTemplate = template
        else:
            self.template = collect_template(self.session, template)

        self.render: DefaultRenderer = DefaultRenderer(self)
        self.render_base = False
        self.ns_type: Optional[NSType] = parent and parent.context.ns_type

        self.react_vars: Dict[str, Set[AnyNode]] = defaultdict(set)
        self.react_nodes: Set[AnyNode] = set()

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement(self.template.name, new_parent)

    @property
    def tag_name(self):
        return self.template.name

    @contextmanager
    def record_reactions(self, node: AnyNode):
        self.locals._hook = lambda item: self.react_vars[item].add(node) or self.react_nodes.add(node)
        HookDict.hook_set()
        yield
        HookDict.hook_clear()
        del self.locals['_hook']

    def select(self, predicate: Union[Iterable[str], Callable[[UniNode], bool]]) -> Generator[UniNode]:
        if isinstance(predicate, typing.Iterable):
            yield from super().select(lambda node: node.tag_name in predicate)
        else:
            yield from super().select(predicate)


    def __getattr__(self, item):
        if hasattr(Context, item):
            return object.__getattribute__(self, item)
        if item in self.locals:
            return self.locals[item]
        else:
            raise AttributeError

    def __setattr__(self, key, value):
        if hasattr(Context, key):
            object.__setattr__(self, key, value)
        else:
            object.__getattribute__(self, 'locals')[key] = value
            if key in self.react_vars:
                for node in frozenset(self.react_vars[key]):
                    node.update()

    def __getitem__(self, item: Union[str, int]):
        if type(item) == int:
            return self.children[item]
        if item in self.locals:
            return self.locals[item]
        return self.parent.context[item] if self.parent else EmptyCaller()

    def __setitem__(self, key, value):
        self.locals[key] = value

    def __str__(self):
        return f'${self.template.name}'


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
    __slots__ = ['tag_name', 'attributes', 'classes', 'con_classes', 'text', 'style',
                 '_set_focus', '_metrics', '_metrics_ev', '_value', '_value_ev'
                 ]

    def __new__(cls, tag_name: str, parent: RenderNode, attributes: Optional[Union[Dict, ADict]] = None, text: str = ''):
        if parent and not parent.context.ns_type:
            return super().__new__(cls)
        instance = super().__new__(NSElement)
        instance.ns_type = parent.context.ns_type
        return instance

    def __init__(self, tag_name: str, parent: RenderNode, attributes: Optional[Union[Dict, ADict]] = None, text: str = ''):
        super().__init__(parent, True)
        self.tag_name: str = tag_name
        self.attributes: ADict = attributes and ADict(attributes) or ADict()
        self.classes: Union[DynamicClasses, DynamicString, str] = DynamicClasses()
        self.con_classes: ConditionalClasses = ConditionalClasses()
        self.style: Union[DynamicStyles, DynamicString, str] = DynamicStyles()
        self.text: Union[DynamicString, str] = text
        self._set_focus = False

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
        self._metrics_ev.wait()

    @property
    def metrics(self):
        if hasattr(self, '_metrics'):
            return self._metrics
        self.request_metrics()
        return self._metrics

    def set_metrics(self, m: Union[MetricsData, Dict[str, Union[int, str]], List[Union[int, str]]], shift: int = 0, grow: int = 0):
        if isinstance(m, dict):
            m = ADict(m)
        elif isinstance(m, list):
            m = ADict({k: v for k, v in zip(['left', 'top', 'width', 'height'], m)})
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

    def __getitem__(self, item: Union[str, int]):
        if type(item) == int:
            return self.children[item]
        return self.context[item]

    def __str__(self):
        return self.tag_name


class NSElement(HTMLElement):
    __slots__ = ['ns_type']

    def __str__(self):
        return f'{NSType(self.ns_type).name}:{self.tag_name}'


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
        return '?'


class LoopNode(RenderNode):
    __slots__ = ['template', 'else_template', 'var_name', 'iterator']

    def __init__(self, parent: RenderNode, template: HTMLTemplate):
        super().__init__(parent, False)

        self.template: Optional[HTMLTemplate] = template
        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None
        self.else_template: Optional[HTMLElement] = None

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement('loop', new_parent)

    @property
    def tag_name(self):
        return 'loop'

    def __str__(self):
        return '⟳'


class TextNode(RenderNode):
    __slots__ = ['text']

    def __init__(self, parent: RenderNode, text: Union[DynamicString, str]):
        super().__init__(parent, True)
        self.text: Union[DynamicString, str] = text

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return TextNode(new_parent, self.text)

    @property
    def tag_name(self):
        return 'text'

    def __str__(self):
        return f'Text'


class EventNode(RenderNode):
    __slots__ = ['attributes']

    def __init__(self, parent: RenderNode, attributes: Optional[ADict] = None):
        super().__init__(parent, True)
        self.attributes = attributes or ADict()

