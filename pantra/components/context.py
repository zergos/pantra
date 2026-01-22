from __future__ import annotations

import typing
from types import CodeType
import threading
from copy import deepcopy
from enum import Enum, auto
from dataclasses import dataclass, field

from ..common import DynamicStyles, DynamicClasses, WebUnits, DynamicString
from ..components.reactdict import ReactDict
from ..oid import get_node
from ..settings import config
from .template import collect_template, HTMLTemplate, get_template_path
from .static import get_static_url
from .render.render_node import RenderNode
from ..compiler import CodeMetrics

if typing.TYPE_CHECKING:
    from typing import *
    from ..session import Session
    from .shot import ContextShot
    from render.renderer_base import ForLoopType

__all__ = ['NSType', 'HTMLTemplate', 'Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode',
           'EventNode', 'SetNode', 'ReactNode', 'ScriptNode', 'ActionType']

ActionType = typing.Callable[['HTMLElement'], None] | None

class NSType(Enum):
    HTML = auto()       # http://www.w3.org/1999/xhtml
    SVG = auto()        # http://www.w3.org/2000/svg
    SVG_EV = auto()     # http://www.w3.org/2001/xml-events
    SVG_XLINK = auto()  # http://www.w3.org/1999/xlink
    MATH = auto()       # http://www.w3.org/1998/Math/MathML


@dataclass(slots=True)
class MetricsData:
    left: int | WebUnits
    top: int | WebUnits
    width: int | WebUnits
    height: int | WebUnits

    def __post_init__(self):
        for k in self.__slots__:
            if not isinstance(v:=getattr(self, k), WebUnits):
                setattr(self, k, WebUnits(v))


@dataclass(slots=True)
class Slot:
    ctx: Context
    template: str | HTMLTemplate | Callable[[RenderNode], None]
    for_reuse: bool
    named_slots: dict[str, Self] = field(default_factory=dict, init=False)

    def get_top(self):
        if self.for_reuse:
            return self.ctx.slot and self.ctx.slot.get_top()
        return self

    def __getitem__(self, name: Union[str, int]) -> Union[Slot, None]:
        if type(name) == str:
            if (slot := self.named_slots.get(name)) is not None:
                if slot.for_reuse:
                    return slot.ctx.slot and slot.ctx.slot[name]
                else:
                    return slot
            return None
        else:
            raise NotImplementedError('integer indexing')  # return super().__getitem__(name)

    def __setitem__(self, name: str, slot: Self):
        self.named_slots[name] = slot

    def __contains__(self, name: str):
        if (slot:=self.named_slots.get(name)) is not None:
            if slot.for_reuse:
                return bool(slot.ctx.slot and name in slot.ctx.slot)
            else:
                return True
        return False

class Context(RenderNode):
    __slots__ = ['locals', '_executed', 'refs', 'slot', 'template', '_restyle', 'ns_type', 'renderer', 'ref_name',
                 'allowed_call', 'code_metrics', 'attributes', 'data_nodes']

    def __init__(self, template_name: str, parent: Optional[RenderNode] = None, shot: Optional[ContextShot] = None, session: Optional[Session] = None, locals: Optional[dict] = None):
        self.attributes: dict[str, Any] = {}
        self.locals: ReactDict = ReactDict()
        if locals:
            self.locals.update(locals)
        self._executed: bool = False
        self.refs: dict[str, Union['Context', HTMLElement, ReactDict]] = {}
        self.ref_name: str | None = None
        self.slot: Optional[Slot] = None
        self.allowed_call: set[str] = set()

        super().__init__(template_name, parent=parent, shot=shot, session=session)

        self.template: Union[HTMLTemplate, CodeType, None] = collect_template(template_name, self.session)
        if self.template is None:
            self.session.error(f'Template `{template_name}` not found')
            raise NameError(f'Template `{template_name}` not found')

        self._restyle: bool = False
        self.ns_type: Optional[NSType] = parent and parent.context.ns_type

        self.code_metrics: Optional[CodeMetrics] = CodeMetrics()
        self.data_nodes: dict[str, RenderNode] | None = None

        self.renderer = config.DEFAULT_RENDERER(self)

    def _clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        return HTMLElement(self.name, new_parent)

    def rebuild(self):
        self.empty()
        self.renderer.build()

    def div(self, classes: str = '', src: Optional[HTMLElement] = None, from_x: int = 0, from_y: int = 0, attributes: Optional[dict, None] = None):
        node = HTMLElement('div', self, attributes)
        node.classes = DynamicClasses(classes)
        if src:
            node.set_metrics(src.metrics, from_x=from_x, from_y=from_y)
        return node

    def get_caller(self, action: str) -> Callable | Awaitable | None:
        method = self.locals.get(action)
        if type(method) is str:
            if method and self.parent:
                return self.parent.get_caller(action)
            return None
        else:
            return method

    def call(self, action: str, *args, **kwargs):
        if (method := self.get_caller(action)) is not None:
            return method(*args, **kwargs)

    def __getitem__(self, item: Union[str, int]) -> Any:
        if type(item) is int:
            return self.children[item]
        return self.locals[item]

    def __setitem__(self, key, value):
        self.locals[key] = value

    def set_quietly(self, key, value):
        self.locals.set_quietly(key, value)

    def __str__(self):
        return f'${self.name}' + (f':{self.ref_name}' if self.ref_name else '')

    def allow_call(self, method: str):
        self.allowed_call.add(method)

    def is_call_allowed(self, method: str) -> bool:
        return method in self.allowed_call or '*' in self.allowed_call

    def has_slot(self, name: str = None) -> bool:
        return bool(self.slot and (not name or name in self.slot))

    def static(self, subdir: str, file_name: str) -> str:
        return get_static_url(self.session.app, get_template_path(self.template), self.name, subdir, file_name)

class ConditionalClass(typing.NamedTuple):
    condition: Callable[[], bool]
    cls: str


class ConditionalClasses(list):
    __slots__ = ['_cache']

    def __init__(self, *args):
        super().__init__(*args)
        self._cache: str = ''

    def update(self):
        if not self:
            return ''
        res = []
        for check in self:
            if check[0]():
                res.append(check[1])
        self._cache = ' '.join(res)
        return self._cache

    def __str__(self):
        if not self:
            return ''
        if not self._cache:
            self.update()
        return self._cache


class HTMLElement(RenderNode):
    render_this = True
    __slots__ = ['ref_name', 'attributes', 'classes', 'con_classes', 'text', 'style', 'data', '_set_focused',
                 '_metrics', '_metrics_ev', 'value_type', '_value', '_value_ev', '_validity', '_validity_ev',
                 'localize']

    def __new__(cls, tag_name: str, parent: RenderNode, attributes: dict[str, Any] | None = None, text: str = '', context: Context = None):
        if not context:
            context = parent and parent.context
        if context and context.ns_type:
            instance = super().__new__(NSElement)
            instance.ns_type = context.ns_type
        else:
            instance = super().__new__(cls)
        return instance

    def __init__(self, tag_name: str, parent: RenderNode, attributes: dict[str, Any] = None, text: str = None, context: Context = None):
        self.ref_name: str | None = None
        self.attributes: dict[str, Any] = attributes or {}
        self.classes: Union[DynamicClasses, DynamicString, str] = DynamicClasses()
        self.con_classes: ConditionalClasses = ConditionalClasses()
        self.style: Union[DynamicStyles, DynamicString, str] = DynamicStyles()
        self.text: Union[DynamicString, str, None] = text
        self.data: dict[str, Any] = {}
        self._set_focused = False
        self.value_type = None
        self.localize: bool = False

        self._metrics: MetricsData | None = None
        self._metrics_ev: threading.Event | None = None
        self._value: Any = None
        self._value_ev: threading.Event | None = None
        self._validity: bool | None = None
        self._validity_ev: threading.Event | None = None
        super().__init__(tag_name, parent, context=context)

    def get_caller(self, action: str) -> Callable | Awaitable | None:
        return self.context.get_caller(action)

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

    def _clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        clone: HTMLElement = HTMLElement(self.name, new_parent)
        clone.attributes = {
            k: v
            for k, v in self.attributes.items() if not k.startswith('on:') and not k.startswith('ref:')
        }
        clone.text = self.text
        clone.classes = deepcopy(self.classes)
        clone.style = deepcopy(self.style)
        clone.localize = self.localize
        return clone

    @staticmethod
    def _set_metrics(oid: int, box: list[int]) -> object:
        self: HTMLElement = get_node(oid)
        if self is None: return
        self._metrics = MetricsData(*box)
        self._metrics_ev.set()

    def request_metrics(self):
        if self._metrics_ev is None:
            self._metrics_ev = threading.Event()
        self.session.request_metrics(self)
        self._metrics_ev.wait(config.LOCKS_TIMEOUT)
        return self._metrics

    @property
    def metrics(self) -> MetricsData:
        if self._metrics is not None:
            return self._metrics
        return self.request_metrics()

    def set_metrics(self, m: Union[MetricsData, dict[str, Union[int, str]], list[Union[int, str]]],
                    from_x: int = 0, from_y: int = 0, shift_x: int = 0, shift_y: int = 0, grow: int = 0):
        if isinstance(m, list):
            m = MetricsData(*m)
        self.style['position'] = 'fixed'
        if from_x:
            m.left = from_x
        self.style['left'] = m.left + shift_x
        if from_y:
            m.top = from_y
        self.style['top'] = m.top + shift_y
        self.style['width'] = m.width + grow
        self.style['height'] = m.height + grow
        self.shot(self)

    @staticmethod
    def _set_value(oid: int, value):
        self: HTMLElement = get_node(oid)
        if self is None: return
        self._value = value
        self._value_ev.set()

    @property
    def value(self):
        if self._value is not object:
            return self._value
        if self._value_ev is None:
            self._value_ev = threading.Event()
        self.session.request_value(self, self.value_type or 'text')
        self._value_ev.wait(config.LOCKS_TIMEOUT)
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.shot(self)

    def validate(self):
        if self._validity_ev is None:
            self._validity_ev = threading.Event()
        self.session.request_validity(self)
        self._validity_ev.wait(config.LOCKS_TIMEOUT)
        return self._validity

    @staticmethod
    def _set_validity(oid: int, validity: bool):
        self: HTMLElement = get_node(oid)
        if self is None: return
        self._validity = validity
        self._validity_ev.set()

    def move_box(self, delta_x, delta_y):
        self.style['left'] += delta_x
        self.style['top'] += delta_y
        self.shot.flick(self)

    def set_focused(self):
        self._set_focused = True

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
        return self.name + (f':{self.ref_name}' if self.ref_name else '')


class NSElement(HTMLElement):
    __slots__ = ['ns_type']

    def __str__(self):
        return f'{NSType(self.ns_type).name}:{self.name}' + (f':{self.ref_name}' if self.ref_name else '')


@dataclass
class Condition:
    __slots__ = ['func', 'template']
    func: Callable[[], bool]
    template: HTMLTemplate | Callable[[RenderNode], None]


class ConditionNode(RenderNode):
    render_if_necessary = True
    __slots__ = ['state', 'conditions', 'template']

    def __init__(self, parent: RenderNode, template: HTMLTemplate):
        self.template = template
        super().__init__('?', parent)
        self.state = -1
        self.conditions: Optional[list[Condition]] = []

    def _clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        return HTMLElement('condition', new_parent)


class LoopNode(RenderNode):
    render_if_necessary = True
    __slots__ = ['template', 'loop_template', 'else_template', 'var_name', 'iterator', 'index_func', 'index_map']

    def __init__(self, parent: RenderNode, template: HTMLTemplate | None):
        self.template: HTMLTemplate | None = template
        super().__init__('@', parent)

        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None
        self.loop_template: Optional[HTMLTemplate | Callable[[RenderNode, ForLoopType, Any, ...], None]] = None
        self.else_template: Optional[HTMLTemplate | Callable[[RenderNode], None]] = None
        self.index_func: Optional[Callable[[ForLoopType, Any], Any]] = None
        self.index_map: dict[Hashable, list[RenderNode]] = {}

    def _clone(self, new_parent: RenderNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement('loop', new_parent)

    def reset_cache(self):
        self.index_map.clear()


class TextNode(RenderNode):
    render_this = True
    __slots__ = ['text']

    def __init__(self, parent: RenderNode, text: Union[DynamicString, str, None]):
        super().__init__('text', parent)
        self.text: Union[DynamicString, str, None] = text

    def _clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        return TextNode(new_parent, self.text)


class EventNode(RenderNode):
    render_this = True
    __slots__ = ['attributes']

    def __init__(self, parent: RenderNode, attributes: dict[str, Any] = None):
        super().__init__('event', parent)
        self.attributes = attributes or {}


class SetNode(RenderNode):
    __slots__ = ['var_name', 'value', 'template']

    def __init__(self, parent: RenderNode, template: Union[HTMLTemplate, Callable[[RenderNode, Any], None]]):
        super().__init__(':=', parent)
        self.template = template
        self.var_name = ''
        self.value = ''


class ReactNode(RenderNode):
    __slots__ = ['var_name', 'action', 'value']

    def __init__(self, parent: RenderNode, var_name: str, action: str):
        super().__init__('>>>', parent)
        self.var_name = var_name
        self.action = action
        self.value = None


class ScriptNode(RenderNode):
    render_this = True
    __slots__ = ['uid', 'attributes', 'text']

    def __init__(self, parent: RenderNode, uid: str, attributes: dict[str, Any] = None, text: str = ''):
        super().__init__('script', parent)
        self.attributes: dict[str, Any] = attributes or {}
        self.text: Union[DynamicString, str] = text
        self.uid: str = uid


class GroupNode(RenderNode):
    __slots__ = ['template']
    def __init__(self, parent: RenderNode, template: HTMLTemplate):
        super().__init__('group', parent)
        self.template = template
