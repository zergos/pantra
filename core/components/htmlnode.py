from types import CodeType
from typing import *

from attrdict import AttrDict

from core.common import DynamicString, UniNode


class HTMLNode(UniNode):
    __slots__ = ('tag_name', 'attributes', 'classes')

    def __init__(self, tag_name: str, parent: Optional['HTMLNode'] = None, attributes: Optional[Union[Dict, AttrDict]] = None):
        super().__init__(parent)
        self.tag_name: str = tag_name
        self.attributes: AttrDict = attributes and AttrDict(attributes) or AttrDict()
        self.classes: Optional[Union[DynamicString, str]] = None

    def __str__(self):
        return self.tag_name


class HTMLTemplate(HTMLNode):
    __slots__ = ('text', 'macro', 'name', 'filename', 'code')

    def __init__(self, tag_name: str, parent: Optional['HTMLTemplate'] = None, attributes: Optional[List[Union[Dict, AttrDict]]] = None, text: str = None):
        super().__init__(tag_name, parent, attributes)
        self.text: str = text
        self.macro: str = ""
        self.name: Optional[str] = None
        self.filename: Optional[str] = None
        self.code: Optional[CodeType] = None

