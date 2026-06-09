from __future__ import annotations

import ast
import typing
from types import CodeType, LambdaType
import threading
from copy import deepcopy
from enum import Enum, auto
from dataclasses import dataclass, field
import inspect
import re

from ..common import DynamicStyles, DynamicClasses, WebUnits, DynamicDict
from ..components.reactdict import ReactDict
from ..settings import config
from .template import collect_template, HTMLTemplate, get_template_path
from .static import get_static_url
from .render.render_node import RenderNode
from ..compiler import CodeMetrics

if typing.TYPE_CHECKING:
    from typing import *
    from ..session import Session
    from .shot import ContextShot
    from .render.renderer_base import ForLoopType, ValueOrCode, RendererBase

__all__ = ['NSType', 'HTMLTemplate', 'Context', 'HTMLElement', 'NSElement', 'LoopNode', 'ConditionNode', 'TextNode',
           'EventNode', 'SetNode', 'ReactNode', 'ScriptNode', 'ActionType', 'AnyNode']

ActionType = typing.Callable[['HTMLElement'], None] | None
CallableTemplate = typing.Union[HTMLTemplate, typing.Callable[[...], None], None]

AnyNode = typing.Union['HTMLElement', 'NSElement', 'Context', 'ConditionNode', 'LoopNode', 'TextNode', 'EventNode',
'SetNode', 'ReactNode', 'ScriptNode']

TAG_PATTERN = re.compile(r"^(\w+)(\s+[a-z_:]+(=(['\"`].*?['\"`]|[^ ]+))?)+$", re.I)
TAG_GROUPS = re.compile(r"^\s+([a-z_:]+)(=(['\"`].*?['\"`]|[^ ]+))?", re.I)

class NSType(Enum):
    """all supported :ref:`namespace <namespaces>` types"""
    HTML = auto()       # http://www.w3.org/1999/xhtml
    SVG = auto()        # http://www.w3.org/2000/svg
    EVENTS = auto()     # http://www.w3.org/2001/xml-events
    XLINK = auto()      # http://www.w3.org/1999/xlink
    MATH = auto()       # http://www.w3.org/1998/Math/MathML


@dataclass(slots=True)
class MeasuresData:
    """represents position and size of the element"""
    left: int | str | WebUnits
    top: int | str | WebUnits
    width: int | str | WebUnits
    height: int | str | WebUnits

    def __post_init__(self):
        for k in self.__slots__:
            if not isinstance(v:=getattr(self, k), WebUnits):
                setattr(self, k, WebUnits(v))


@dataclass(slots=True)
class Slot:
    ctx: Context
    template: str | HTMLTemplate | Callable[[...], None]
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
    """Context of the component.

    Attributes:
          name (str): name of this component
          attributes (DynamicDict): initial attributes defined with component
          locals (ReactDict): context local variables, evaluated by Python script
          refs (dict[str, 'Context' | HTMLElement]): :ref:`references <ref>` to named nodes
          ref_name (str): reference name if specified
          template (HTMLTemplate | CodeType): template to build component context
          ns_type (NSType): :ref:`namespace <namespaces>` ID
          code_metrics (CodeMetrics): code metrics of the Python script
          data_nodes (dict[str, RenderNode]): collection of :ref:`data nodes <data nodes>`
          renderer (RenderBase): associated :doc:`renderer <renderer>`
          allowed_call (set[str]): set of allowed function names
    """
    __slots__ = ['locals', '_executed', 'refs', 'slot', 'template', '_restyle', 'ns_type', 'renderer', 'ref_name',
                 'allowed_call', 'code_metrics', 'attributes', 'data_nodes', 'name']

    def __init__(self, template_name: str, parent: Optional[RenderNode] = None, shot: Optional[ContextShot] = None, session: Optional[Session] = None, locals: Optional[dict] = None):
        self.name: str = template_name
        self.attributes: DynamicDict = DynamicDict()
        self.locals: ReactDict = ReactDict()
        if locals:
            self.locals.update(locals)
        self._executed: bool = False
        self.refs: dict[str, Union['Context', HTMLElement]] = {}
        self.ref_name: str | None = None
        self.slot: Optional[Slot] = None
        self.allowed_call: set[str] = set()

        super().__init__(parent=parent, shot=shot, session=session)

        self.template: Union[HTMLTemplate, CodeType, None] = collect_template(template_name, self.session)
        if self.template is None:
            self.session.error(f'Component `{template_name}` load error')
            raise NameError(f'Component `{template_name}` load error')

        self._restyle: bool = False
        self.ns_type: Optional[NSType] = parent and parent.context.ns_type

        self.code_metrics: Optional[CodeMetrics] = CodeMetrics()
        self.data_nodes: dict[str, RenderNode] | None = None

        self.renderer: RendererBase = config.DEFAULT_RENDERER(self)

    def _frozen_clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        return HTMLElement(self.name, new_parent)

    def rebuild(self):
        """clear component and build from template"""
        self.empty()
        self.renderer.build()

    def div(self, classes: str = '', src: Optional[HTMLElement] = None, from_x: int = 0, from_y: int = 0, attributes: Optional[dict, None] = None):
        """add positioned <div> container

        Usually used to make temporary box to visualize drag-and-drop.

        Arguments:
            classes (str): classes list separated by space
            src (HTMLElement): source HTML element for box metrics
            from_x (int): x coordinate to move source box
            from_y (int): y coordinate to move source box
            attributes (dict[str, Any]): any other custom attributes of container
        """
        node = HTMLElement('div', self, attributes)
        node.classes = DynamicClasses(classes)
        if src:
            node.set_measures(src.measures, from_x=from_x, from_y=from_y)
        return node

    def get_caller(self, action: str) -> Callable | Awaitable | None:
        """get callable local action by name"""
        method = self.locals.get(action)
        if method is not None and not callable(method) and not inspect.iscoroutinefunction(method):
            raise RuntimeError(f'method `{action}` is not callable or awaitable')
        return method

    def call(self, action: str, *args, **kwargs):
        """call local action by name"""
        if (method := self.get_caller(action)) is not None:
            return method(*args, **kwargs)
        return None

    def __getitem__(self, item: str) -> Any:
        """shortcut to get local context variables"""
        return self.locals[item]

    def __setitem__(self, key, value):
        """shortcut to set local context variables"""
        self.locals[key] = value

    def set_quietly(self, key, value):
        """shortcut to set local context variables quietly"""
        self.locals.set_quietly(key, value)

    def __str__(self):
        return f'${self.name}' + (f':{self.ref_name}' if self.ref_name else '')

    def allow_call(self, method: str):
        """add method name to allowed calls set for JS :doc:`callback <js_callback>`"""
        self.allowed_call.add(method)

    def is_call_allowed(self, method: str) -> bool:
        """check if method is allowed for JS :doc:`callback <js_callback>`"""
        return method in self.allowed_call or '*' in self.allowed_call

    def has_slot(self, name: str = None) -> bool:
        """check if component has slot by name"""
        return bool(self.slot and (not name or name in self.slot))

    def static(self, subdir: str, file_name: str) -> str:
        """get URL for static file"""
        return get_static_url(self.session.app, get_template_path(self.template), self.name, subdir, file_name)


class HTMLElement(RenderNode):
    """HTML element node

    Attributes:
        name (str): name of this HTML tag
        attributes (DynamicDict): HTML node attributes
        classes (DynamicClasses): HTML classes
        style (DynamicStyles): CSS style attributes
        data (DynamicDict): custom node data
        value_type (str): HTML "type" attribute
        ref_name (str): reference name if specified
        localize (bool): localize time and date values, read :ref:`for more <localize>`
        text (str): text
    """

    render_this = True
    __slots__ = ['name', 'ref_name', 'attributes', 'classes', 'text', 'style', 'data', '_set_focused',
                 '_measures', '_measures_ev', 'value_type', '_value', '_value_ev', '_validity', '_validity_ev',
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
        self.name = tag_name
        self.ref_name: str | None = None
        self.attributes: DynamicDict = DynamicDict(attributes) if attributes else DynamicDict()
        self.classes: DynamicClasses | str = DynamicClasses()
        self.style: DynamicStyles | str = DynamicStyles()
        self.text: str = text
        self.data: DynamicDict = DynamicDict()
        self._set_focused = False
        self.value_type = None
        self.localize: bool = False

        self._measures: MeasuresData | None = None
        self._measures_ev: threading.Event | None = None
        self._value: Any = None
        self._value_ev: threading.Event | None = None
        self._validity: bool | None = None
        self._validity_ev: threading.Event | None = None
        super().__init__(parent, context=context)

    def get_caller(self, action: str) -> Callable | Awaitable | None:
        """get context caller by name"""
        return self.context.get_caller(action)

    @classmethod
    def parse(cls, element: str, parent: RenderNode, text: str = '') -> Optional[HTMLElement]:
        """create HTMLElement from string

        Example::

            div = HTMLElement.parse('input type=text value="Hello"', parent)
        """
        if (g:=TAG_PATTERN.match(element)) is None:
            raise ValueError(f'invalid HTML element: <{element}>')
        tag_name = g[1]
        attributes = {}
        for attr in TAG_GROUPS.finditer(element):
            attr_name = attr[0]
            try:
                attributes[attr_name] = ast.literal_eval(attr[2])
            except (ValueError, SyntaxError):
                attributes[attr_name] = attr[2]
        return HTMLElement(tag_name, parent, attributes, text)

    def _frozen_clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        clone: HTMLElement = HTMLElement(self.name, new_parent)
        clone.attributes = DynamicDict({
            k: v
            for k, v in self.attributes.items() if not k.startswith('on:') and not k.startswith('ref:')
        })
        clone.text = self.text
        clone.classes = deepcopy(self.classes)
        clone.style = deepcopy(self.style)
        clone.localize = self.localize
        return clone

    def _set_measures(self, box: list[int]) -> object:
        self._measures = MeasuresData(*box)
        self._measures_ev.set()

    def request_measures(self):
        """get position and size of this element, rendered in user browser

        Warning:
             Take in account `getBoundingClientRect() <https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect>`__
             repeated calls side effect.
        """
        if self._measures_ev is None:
            self._measures_ev = threading.Event()
        self.session.request_measures(self)
        self._measures_ev.wait(config.LOCKS_TIMEOUT)
        return self._measures

    @property
    def measures(self) -> MeasuresData:
        """get cached position and size of this element, rendered in user browser

        Measures is cached after the first request. To update call :meth:`request_measures`.
        """
        if self._measures is not None:
            return self._measures
        return self.request_measures()

    def set_measures(self, m: Union[MeasuresData, list[Union[int, str]]],
                     from_x: int = 0, from_y: int = 0, shift_x: int = 0, shift_y: int = 0, grow: int = 0):
        """change this element position and size in user browser

        Calling this method sets `position: fixed` style of element, and then changed metrics

        Arguments:
            m: :class:`MeasuresData` or sequential list of metrics
            from_x: new x position
            from_y: new y position
            shift_x: shift x position
            shift_y: shift y position
            grow: grow width and height by amount of units
        """
        if isinstance(m, list):
            m = MeasuresData(*m)
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

    def reset_measures(self):
        """reset measures cache"""
        self._measures = None

    def _set_value(self, value):
        self._value = value
        self._value_ev.set()

    @property
    def value(self):
        """request value of this element <input> from user browser

        It cached once requested.
        """
        if self._value is not object:
            return self._value
        if self._value_ev is None:
            self._value_ev = threading.Event()
        self.session.request_value(self, self.value_type or 'text')
        self._value_ev.wait(config.LOCKS_TIMEOUT)
        return self._value

    @value.setter
    def value(self, value):
        """send new value to user browser"""
        self._value = value
        self.shot(self)

    def validate(self):
        """check `validity state <https://developer.mozilla.org/en-US/docs/Web/API/ValidityState>`__ of this element"""
        if self._validity_ev is None:
            self._validity_ev = threading.Event()
        self.session.request_validity(self)
        self._validity_ev.wait(config.LOCKS_TIMEOUT)
        return self._validity

    def _set_validity(self, validity: bool):
        self._validity = validity
        self._validity_ev.set()

    def move_box(self, delta_x, delta_y):
        """shift element location by delta_x, delta_y

        Designed for drag'n'drop
        """
        if not isinstance(self.style, DynamicStyles):
            self.style = DynamicStyles(self.style)
        self.style['left'] += delta_x
        self.style['top'] += delta_y
        self.shot.flick(self)

    def set_focused(self):
        """mark this element as focused

        This state reset after send.
        """
        self._set_focused = True

    def add_class(self, class_name):
        """shortcut for `classes += class_name` and update"""
        self.classes += class_name
        self.shot(self)

    def remove_class(self, class_name):
        """shortcut for `classes -= class_name` and update"""
        self.classes -= class_name
        self.shot(self)

    def toggle_class(self, class_name):
        """shortcut for `classes *= class_name` and update"""
        self.classes *= class_name
        self.shot(self)

    def set_text(self, text: str):
        """set text and update"""
        self.text = text
        self.shot(self)

    def __getitem__(self, item: Union[str, int]):
        """shortcut to get variable value from local context"""
        return self.context[item]

    def __setitem__(self, key, value):
        """shortcut to set variable value in local context"""
        self.context[key] = value

    def set_quietly(self, key, value):
        """shortcut to set variable value suppressing reactions in local context"""
        self.context.set_quietly(key, value)

    def reset_loop_cache(self):
        """reset :class:`LoopNode` cache for all child nodes"""
        for node in self.select("@", depth=1):
            node.reset_cache()

    def __str__(self):
        return self.name + (f':{self.ref_name}' if self.ref_name else '')


class NSElement(HTMLElement):
    """Extension to :class:`HTMLElement` with :ref:`namespace <namespaces>` support

    Attributes:
        ns_type (NSType): namespace type
    """
    __slots__ = ['ns_type']

    def __str__(self):
        return f'{NSType(self.ns_type).name}:{self.name}' + (f':{self.ref_name}' if self.ref_name else '')


@dataclass
class Condition:
    __slots__ = ['func', 'template']
    func: Callable[[], bool]
    template: CallableTemplate


class ConditionNode(RenderNode):
    """Node for conditional `{{#if ...}}`, `{{#elif ...}}`, `{{#else}}`"""
    __slots__ = ['state', 'conditions', 'template']

    def __init__(self, parent: RenderNode, template: Optional[HTMLTemplate]):
        self.template = template
        super().__init__(parent)
        self.state = -1
        self.conditions: Optional[list[Condition]] = []

    def __str__(self):
        return '?'

    def _frozen_clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        return HTMLElement('condition', new_parent)


class LoopNode(RenderNode):
    """Node for loops `{{#for ...}}`"""
    __slots__ = ['template', 'loop_template', 'else_template', 'var_name', 'iterator', 'index_func', 'index_map']

    def __init__(self, parent: RenderNode, template: Optional[HTMLTemplate]):
        self.template: CallableTemplate = template
        super().__init__(parent)

        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None
        self.loop_template: CallableTemplate = None
        self.else_template: CallableTemplate = None
        self.index_func: Optional[Callable[[ForLoopType, Any], Any]] = None
        self.index_map: dict[Hashable, list[RenderNode]] = {}

    def __str__(self):
        return '@'

    def _frozen_clone(self, new_parent: RenderNode) -> Optional[HTMLElement, TextNode]:
        return HTMLElement('loop', new_parent)

    def reset_cache(self):
        """reset index cache"""
        self.index_map.clear()


class TextNode(RenderNode):
    """node for raw text content

    intended to render sliced text blocks:

    ..  code-block:: pantra

        <div>
            Text one
            <p>...</p>
            {{get_content()}}
            <p>...</p>
            Text three
        </div>
    """
    render_this = True
    __slots__ = ['factory', 'text']

    def __init__(self, parent: RenderNode, text: ValueOrCode):
        super().__init__(parent)
        if isinstance(text, LambdaType):
            self.factory: Callable[[], None] | None = text
            self.text: str = text()
        else:
            self.factory = None
            self.text = text

    def __str__(self):
        return 'text'

    def refresh(self):
        if self.factory is not None:
            self.text = self.factory()
            self.update()

    def _frozen_clone(self, new_parent: RenderNode) -> Union[HTMLElement, TextNode]:
        return TextNode(new_parent, self.text)


class EventNode(RenderNode):
    """:ref:`Event <events>` node"""
    render_this = True
    __slots__ = ['selector', 'events']

    def __init__(self, parent: RenderNode, selector: str | None = None, events: DynamicDict = None):
        super().__init__(parent)
        self.selector: str | None = selector
        self.events: DynamicDict = events or DynamicDict()

    def __str__(self):
        return 'event'


class SetNode(RenderNode):
    """:ref:`Set node <set node>`"""
    __slots__ = ['variables', 'template', 'scoped', 'self_clear']

    def __init__(self, parent: RenderNode, template: CallableTemplate):
        super().__init__(parent)
        self.template: CallableTemplate = template
        self.variables: DynamicDict = DynamicDict(_lazy_mode=True)
        self.scoped: bool = False
        self.self_clear: bool = False

    def __str__(self):
        return ':='


class ReactNode(RenderNode):
    """:ref`React node <reactive tag>`"""
    __slots__ = ['var_name', 'action', 'value']

    def __init__(self, parent: RenderNode, var_name: str, action: str | Callable[[...], None]):
        super().__init__(parent)
        self.var_name = var_name
        self.action = action
        self.value = None

    def __str__(self):
        return f'!{self.var_name}'


class ScriptNode(RenderNode):
    """JavaScript node"""
    render_this = True
    __slots__ = ['uid', 'attributes', 'text', 'put_to_head']

    def __init__(self, parent: RenderNode, uid: str, attributes: dict[str, Any] = None, text: str = '',
                 put_to_head: bool = True):
        super().__init__(parent)
        self.attributes: dict[str, Any] = attributes or {}
        self.text: str = text
        self.uid: str = uid
        self.put_to_head: bool = put_to_head

    def __str__(self):
        return 'script'


class GroupNode(RenderNode):
    """Helper group node"""
    __slots__ = ['template']
    def __init__(self, parent: RenderNode, template: Optional[HTMLTemplate]):
        super().__init__(parent)
        self.template = template

    def __str__(self):
        return 'group'
