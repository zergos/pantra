from __future__ import annotations

from copy import deepcopy
from enum import Enum, auto
from typing import *
from dataclasses import dataclass

from attrdict import AttrDict

from ..common import DynamicStyles, AnyNode, EmptyCaller
from .htmlnode import HTMLNode, HTMLTemplate, collect_template

from .render import RenderMixin, DefaultRenderer

if TYPE_CHECKING:
    from ..common import DynamicString
    from .render import ContextShot
    from ..session import Session


class NSType(Enum):
    HTML = auto()       # http://www.w3.org/1999/xhtml
    SVG = auto()        # http://www.w3.org/2000/svg
    SVG_EV = auto()     # http://www.w3.org/2001/xml-events
    SVG_XLINK = auto()  # http://www.w3.org/1999/xlink
    MATH = auto()       # http://www.w3.org/1998/Math/MathML


class Slot(NamedTuple):
    ctx: 'Context'
    template: HTMLTemplate


class Context(AnyNode, RenderMixin):
    __slots__ = ['locals', 'server_events', 'refs', 'slot', 'template', 'render', 'render_base', 'ns_type']

    def __init__(self, template: Union[HTMLTemplate, str], parent: Optional[AnyNode] = None, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        self.locals = AttrDict()
        self.server_events = AttrDict()
        self.refs: Dict[str, Union['Context', HTMLElement]] = AttrDict()
        self.slot: Optional[Slot] = None

        super().__init__(parent=parent)

        RenderMixin.__init__(self, parent, shot=shot, session=session)

        if type(template) == HTMLTemplate:
            self.template: HTMLTemplate = template
        else:
            self.template = collect_template(self.session, template)

        self.render: DefaultRenderer = DefaultRenderer(self)
        self.render_base = False
        self.ns_type: Optional[NSType] = parent and parent.context.ns_type

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


class HTMLElement(HTMLNode, RenderMixin):
    __slots__ = ['text', 'style']

    def __new__(cls, tag_name: str, parent: AnyNode, attributes: Optional[Union[Dict, AttrDict]] = None, text: str = '', **kwargs):
        if parent and not parent.context.ns_type:
            return super().__new__(cls)
        instance = super().__new__(NSElement)
        instance.ns_type = parent.context.ns_type
        return instance

    def __init__(self, tag_name: str, parent: AnyNode, attributes: Optional[Union[Dict, AttrDict]] = None, text: str = '', **kwargs):
        super().__init__(tag_name=tag_name, parent=parent, attributes=attributes)
        RenderMixin.__init__(self, parent, **kwargs)
        self.style: Union[DynamicStyles, DynamicString, str] = DynamicStyles()
        self.text: Union[str, DynamicString] = text

    def render(self, content: Union[str, AnyNode]):
        self.context.render(self, content)

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


class ConditionNode(AnyNode, RenderMixin):
    __slots__ = ['state', 'conditions']

    def __init__(self, parent: AnyNode):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)
        self.state = -1
        self.conditions: Optional[List[Condition]] = []

    @property
    def tag_name(self):
        return 'condition'

    def __str__(self):
        return f'Condition {self.oid}'


class LoopNode(AnyNode, RenderMixin):
    __slots__ = ['template', 'var_name', 'iterator']

    def __init__(self, parent: AnyNode, template: HTMLTemplate):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)

        self.template: Optional[HTMLTemplate] = template
        self.var_name: Optional[str] = None
        self.iterator: Optional[Callable[[], Iterable]] = None

    @property
    def tag_name(self):
        return 'loop'

    def __str__(self):
        return f'Loop {self.oid}'


class TextNode(AnyNode, RenderMixin):
    __slots__ = ['text']

    def __init__(self, parent: AnyNode, text: str):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)
        self.text: str = text

    @property
    def tag_name(self):
        return 'text'

    def __str__(self):
        return f'Text {self.oid}'


class EventNode(AnyNode, RenderMixin):
    __slots__ = ['attributes']

    def __init__(self, parent: AnyNode, attributes: Optional[AttrDict] = None):
        super().__init__(parent=parent)
        RenderMixin.__init__(self, parent)
        self.attributes = attributes or AttrDict()