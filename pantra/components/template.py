from __future__ import annotations

import typing
from enum import Enum, IntEnum, auto
from pathlib import Path
import re
from dataclasses import dataclass
import ast

from pantra.common import UniNode
from pantra.settings import config

if typing.TYPE_CHECKING:
    from typing import Self, Optional, Any
    from types import CodeType

    from pantra.session import Session
    from pantra.compiler import CodeMetrics

__all__ = ['HTMLTemplate', 'MacroCode', 'collect_styles', 'collect_template', 'NodeType', 'AttrType', 'MacroType']

templates: dict[str, HTMLTemplate | None] = {}

def is_expression_id(expr: str) -> str:
    # check expression is field "name"
    return is_expression_id.r.fullmatch(expr) is not None

is_expression_id.r = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]+")

def is_expression_canonical(expr: str) -> bool:
    # check expression is "some.field.name"
    return (is_expression_canonical.r.fullmatch(expr) is not None
        and not expr.startswith("this") and not expr.startswith("node"))

is_expression_canonical.r = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]+([.][a-zA-Z_][a-zA-Z0-9_]+)+$")

class NodeType(IntEnum):
    HTML_TAG = auto()
    TEMPLATE_TAG = auto()
    ROOT_NODE = auto()
    MACRO_IF = auto()
    MACRO_FOR = auto()
    MACRO_SET = auto()
    MACRO_INTERNAL = auto()
    AT_COMPONENT = auto()
    AT_SLOT = auto()
    AT_PYTHON = auto()
    AT_SCRIPT = auto()
    AT_STYLE = auto()
    AT_EVENT = auto()
    AT_SCOPE = auto()
    AT_TEXT = auto()
    AT_MACRO = auto()
    AT_REACT = auto()

    @staticmethod
    def detect(tag_name: str) -> NodeType:
        if tag_name[0].islower():
            return NodeType.HTML_TAG
        if tag_name[0].isupper():
            return NodeType.TEMPLATE_TAG
        if tag_name[0] == '$':
            return NodeType.ROOT_NODE
        if tag_name[0] == '#':
            if tag_name == '#if':
                return NodeType.MACRO_IF
            if tag_name == '#for':
                return NodeType.MACRO_FOR
            if tag_name == '#set':
                return NodeType.MACRO_SET
            return NodeType.MACRO_INTERNAL
        if tag_name[0] == '@':
            return getattr(NodeType, 'AT_' + tag_name[1:].upper())
        raise ValueError(f"Undetected TAG `{tag_name}`")

class AttrType(IntEnum):
    ATTR = auto()
    REF_NAME = auto()
    CREF_NAME = auto()
    SCOPE = auto()
    ON_RENDER = auto()
    ON_INIT = auto()
    CLASS_SWITCH = auto()
    DYNAMIC_STYLE = auto()
    BIND_VALUE = auto()
    DYNAMIC_SET = auto()
    DATA = auto()
    SRC_HREF = auto()
    REACTIVE = auto()
    STYLE = auto()
    CLASS = auto()
    TYPE = auto()
    VALUE = auto()
    LOCALIZE = auto()
    SET_FALSE = auto()
    CONSUME = auto()
    DATA_NODE = auto()

    @staticmethod
    def detect(attr: str) -> tuple[AttrType, str | None, bool]:
        if ':' in attr:
            if attr.startswith('ref:'):
                name = attr.split(':')[1].strip()
                return AttrType.REF_NAME, name, False
            if attr.startswith('cref:'):
                name = attr.split(':')[1].strip()
                return AttrType.CREF_NAME, name, False
            if attr.startswith('scope:'):
                name = attr.split(':')[1].strip()
                return AttrType.SCOPE, name, False
            if attr == 'on:render':
                return AttrType.ON_RENDER, None, False
            if attr == 'on:init':
                return AttrType.ON_INIT, None, False
            if attr.startswith('class:'):
                cls = attr.split(':')[1].strip()
                return AttrType.CLASS_SWITCH, cls, True
            if attr.startswith('css:'):
                attr = attr.split(':')[1].strip()
                return AttrType.DYNAMIC_STYLE, attr, True
            if attr == 'bind:value':
                return AttrType.BIND_VALUE, None, False
            if attr.startswith('set:'):
                attr = attr.split(':')[1].strip()
                return AttrType.SET_FALSE, attr, True
            if attr.startswith('data:'):
                attr = attr.split(':')[1].strip()
                return AttrType.DATA, attr, False
            if attr.startswith('src:') or attr.startswith('href:'):
                return AttrType.SRC_HREF, attr, False
            if attr.startswith('not:'):
                attr = attr.split(':')[1].strip()
                return AttrType.SET_FALSE, attr, True
        else:
            if attr == 'reactive':
                return AttrType.REACTIVE, None, False
            if attr == 'style':
                return AttrType.STYLE, None, False
            if attr == 'class':
                return AttrType.CLASS, None, False
            if attr == 'type':
                return AttrType.TYPE, None, False
            if attr == 'value':
                return AttrType.VALUE, None, False
            if attr == 'localize':
                return AttrType.LOCALIZE, None, False
            if attr == 'consume':
                return AttrType.CONSUME, None, False
            if attr == 'data-node':
                return AttrType.DATA_NODE, None, False
        return AttrType.ATTR, attr, False

class MacroType(Enum):
    STRING = auto()
    TEMPLATE = auto()
    BOOLEAN = auto()
    VALUE = auto()
    ITERATOR = auto()
    INDEX = auto()

class AstNamesVisitor(ast.NodeVisitor):
    def __init__(self):
        self.vars = set()
    def visit_Name(self, node):
        self.vars.add(node.id)

@dataclass(slots=True)
class MacroCode:
    type: MacroType
    reactive: bool
    code: CodeType | list[str] | None
    src: str
    vars: set[str] = None

    def __post_init__(self) -> None:
        visitor = AstNamesVisitor()
        visitor.visit(ast.parse(self.src))
        self.vars = visitor.vars

        if is_expression_id(self.src):
            self.code = [self.src]
        elif is_expression_canonical(self.src):
            self.code = self.src.split('.')

class HTMLTemplate(UniNode):
    __slots__ = ('tag_name', 'node_type', 'attributes', 'attr_specs', 'content', 'name', 'filename', 'code',
                 'index', 'hex_digest', 'code_metrics')

    def __init__(self, tag_name: str, index: int, parent: Self | None = None, attributes: dict | None = None, text: str = None):
        super().__init__(parent)
        self.tag_name: str = tag_name
        self.node_type: NodeType = NodeType.detect(tag_name)
        self.attributes: dict[str, str | MacroCode | None] = attributes or {}
        self.attr_specs: dict[str, tuple[AttrType, str | None, bool]] = {k: AttrType.detect(k) for k in self.attributes}
        self.content: str | MacroCode | None = text
        self.name: str | None = None
        self.filename: Optional[Path] = None
        self.code: str | CodeType | None = None
        self.code_metrics: Optional[CodeMetrics] = None
        self.index: int = index
        self.hex_digest: str = ''

    def fold(self) -> Self:
        res = HTMLTemplate('@component', 0, None)
        res._parent = self
        res._children = self._children
        self._children = [res]
        for child in res._children:
            child._parent = res
        return res

    def __str__(self):
        return self.tag_name

    def set_attr(self, attr_name: str, attr_value: Any):
        self.attributes[attr_name] = attr_value
        self.attr_specs[attr_name] = AttrType.detect(attr_name)


def _search_component(path: Path, name: str) -> Path | None:
    for file in path.glob(f"**/{name}.html"):
        return file
    return None


def collect_template(name: str, session: Optional[Session] = None, app: Optional[str] = None) -> Optional[HTMLTemplate]:
    global templates

    key = session.app +  '/' + name if session is not None else name
    if key in templates:
        return templates[key]

    path = _search_component(session.app_path, name) if session is not None \
        else _search_component(config.APPS_PATH / app, name) if app is not None \
        else None
    if not path:
        if name in templates:
            templates[key] = templates[name]
            return templates[name]
        #elif config.PRODUCTIVE:
        #    templates[key] = None
        #    return None

        path = _search_component(config.COMPONENTS_PATH, name)
        if not path:
            if not config.PRODUCTIVE and session is not None:
                session.error(f'component {name} not found')
            templates[key] = None
            return None
        key = name

    from .loader import load
    template = load(path, session.error) if session is not None else load(path, lambda x: None)
    if template:
        template.name = name
        templates[key] = template
    return template

def collect_styles(app:str, app_path: Path, error_callback: typing.Callable[[str], None]) -> str:
    from .loader import load_styles

    styles = []
    for file in app_path.glob('**/*.html'):
        if file == config.BOOTSTRAP_FILENAME:
            continue
        try:
            res = load_styles(app, file.stem, file)
        except Exception as e:
            error_callback(f'{file}> Style collector> {e}')
        else:
            if res:
                styles.append(res)

    return '\n'.join(styles)

