from __future__ import annotations

import os
from types import CodeType
from typing import *

from attrdict import AttrDict

from core.common import DynamicString, AnyNode
from core.defaults import COMPONENTS_PATH

if TYPE_CHECKING:
    from core.session import Session

from logging import getLogger
logger = getLogger(__name__)

templates: Dict[str, 'HTMLTemplate'] = {}


class HTMLNode(AnyNode):
    __slots__ = ('tag_name', 'attributes', 'classes')

    def __init__(self, tag_name: str, parent: Optional['HTMLNode'] = None, children: Optional[List['HTMLNode']] = None, attributes: Optional[Union[Dict, AttrDict]] = None):
        super().__init__(parent, children)
        self.tag_name: str = tag_name
        self.attributes: AttrDict = attributes and AttrDict(attributes) or AttrDict()
        self.classes: Optional[Union[DynamicString, str]] = None

    def __str__(self):
        return self.tag_name


class HTMLTemplate(HTMLNode):
    __slots__ = ('text', 'macro', 'name', 'filename', 'code')

    def __init__(self, tag_name: str, parent: Optional['HTMLTemplate'] = None, children: Optional[List['HTMLTemplate']] = None, attributes: Optional[List[Union[Dict, AttrDict]]] = None, text: str = None):
        super().__init__(tag_name, parent, children, attributes)
        self.text: str = text
        self.macro: str = ""
        self.name: Optional[str] = None
        self.filename: Optional[str] = None
        self.code: Optional[CodeType] = None


def _search_component(path, name):
    for root, dirs, files in os.walk(path):
        for file in files:  # type: str
            if file.endswith('html'):
                if os.path.basename(file) == f'{name}.html':
                    return os.path.join(root, file)
    return None


def collect_template(session: Session, name) -> Optional[HTMLTemplate]:
    import core.components.loader as loader
    global templates

    if name in templates:
        return templates[name]

    path = _search_component(session.app, name)
    if not path:
        path = _search_component(COMPONENTS_PATH, name)
        if not path:
            logger.warning(f'component {name} not found')
            return None

    templates[name] = loader.load(path)
    if templates[name]:
        templates[name].name = name
    return templates[name]
    '''
    try:
        templates[name] = loader.load(path)
        if templates[name]:
            templates[name].name = name
    except Exception as e:
        logger.error(f'component {name} parse exception {e}')
        return None
    else:
        return templates[name]
    '''


def collect_styles(app_path) -> str:
    import core.components.loader as loader
    styles = []
    for root, dirs, files in os.walk(app_path):
        for file in files:  # type: str
            if file.endswith('html'):
                name, ext = os.path.splitext(file)
                path = os.path.join(root, file)
                res = loader.load_styles(name, path)
                if res:
                    styles.append(res)

    return '\n'.join(styles)

