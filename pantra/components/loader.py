from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
import re
import typing
from enum import IntEnum, auto

import cssutils
import sass
from antlr4 import FileStream, CommonTokenStream, IllegalStateException
from antlr4.error.ErrorListener import ErrorListener
from cssutils.css import CSSMediaRule, CSSStyleRule

from .grammar.PMLLexer import PMLLexer
from .grammar.PMLParser import PMLParser
from .grammar.PMLParserVisitor import PMLParserVisitor

from ..common import UniNode, ADict
from ..settings import config

if typing.TYPE_CHECKING:
    from ..session import Session
    from typing import *
    from types import CodeType

__all__ = ['MacroCode', 'HTMLTemplate', 'collect_styles', 'collect_template', 'get_static_url', 'NodeType', 'AttrType']

VOID_ELEMENTS = 'area base br col embed hr img input link meta param source track wbr'.split()
SPECIAL_ELEMENTS = 'slot event scope react component'.split()
FORMATTED_EXPRESSION = re.compile(r'^([^{]|\{\{)*\{([^}]|\{\{|}})*}(?!})')

templates: typing.Dict[str, HTMLTemplate | None] = {}

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
    NO_SPECIAL = auto()
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

    @staticmethod
    def detect(attr: str) -> tuple[AttrType, str | None]:
        if ':' in attr:
            if attr.startswith('ref:'):
                name = attr.split(':')[1].strip()
                return AttrType.REF_NAME, name
            if attr.startswith('cref:'):
                name = attr.split(':')[1].strip()
                return AttrType.CREF_NAME, name
            if attr.startswith('scope:'):
                name = attr.split(':')[1].strip()
                return AttrType.SCOPE, name
            if attr == 'on:render':
                return AttrType.ON_RENDER, None
            if attr == 'on:init':
                return AttrType.ON_INIT, None
            if attr.startswith('class:'):
                cls = attr.split(':')[1].strip()
                return AttrType.CLASS_SWITCH, cls
            if attr.startswith('css:'):
                attr = attr.split(':')[1].strip()
                return AttrType.DYNAMIC_STYLE, attr
            if attr == 'bind:value':
                return AttrType.BIND_VALUE, None
            if attr.startswith('set:'):
                attr = attr.split(':')[1].strip()
                return AttrType.SET_FALSE, attr
            if attr.startswith('data:'):
                attr = attr.split(':')[1].strip()
                return AttrType.DATA, attr
            if attr.startswith('src:') or attr.startswith('href:'):
                return AttrType.SRC_HREF, attr
            if attr.startswith('not:'):
                attr = attr.split(':')[1].strip()
                return AttrType.SET_FALSE, attr
        else:
            if attr == 'reactive':
                return AttrType.REACTIVE, None
            if attr == 'style':
                return AttrType.STYLE, None
            if attr == 'class':
                return AttrType.CLASS, None
            if attr == 'type':
                return AttrType.TYPE, None
            if attr == 'value':
                return AttrType.VALUE, None
            if attr == 'localize':
                return AttrType.LOCALIZE, None
            if attr == 'consume':
                return AttrType.CONSUME, None
        return AttrType.NO_SPECIAL, None


class MacroCode(typing.NamedTuple):
    reactive: bool
    code: CodeType | None
    src: str


class HTMLTemplate(UniNode):
    code_base: Dict[str, CodeType] = {}
    __slots__ = ('tag_name', 'node_type', 'attributes', 'attr_specs', 'text', 'macro', 'name', 'filename', 'code', 'index', 'hex_digest')

    def __init__(self, tag_name: str, index: int, parent: Optional['HTMLTemplate'] = None, attributes: Dict | ADict | None = None, text: str = None):
        super().__init__(parent)
        self.tag_name: str = tag_name
        self.node_type: NodeType = NodeType.detect(tag_name)
        self.attributes: Dict[str, str | MacroCode | None] = attributes and ADict(attributes) or ADict()
        self.attr_specs: Dict[str, tuple[AttrType, str | None]] = \
            {k: AttrType.detect(k) for k in self.attributes}
        self.text: str = text
        self.macro: MacroCode | list[MacroCode] | None = None
        self.name: Optional[str] = None
        self.filename: Optional[Path] = None
        self.code: Optional[Union[CodeType, str]] = None
        self.index: int = index
        self.hex_digest: str = ''

    def __str__(self):
        return self.tag_name

    def set_attr(self, attr_name: str, attr_value: Any):
        self.attributes[attr_name] = attr_value
        self.attr_specs[attr_name] = AttrType.detect(attr_name)


class HTMLVisitor(PMLParserVisitor):

    def __init__(self, filename: Path):
        name = Path(filename).stem
        root = HTMLTemplate(f'${name}', 0)
        root.filename = filename
        self.root: typing.Optional[HTMLTemplate] = root
        self.current: typing.Optional[HTMLTemplate] = root
        self.cur_attr: typing.Optional[str] = None
        self._index = 0

    @property
    def index(self):
        self._index += 1
        return self._index

    def visitText(self, ctx: PMLParser.TextContext):
        text = ctx.getText().strip('\uFEFF')
        if text.strip() and self.current != self.root:
            if text.startswith('#'):
                text = re.sub(r'\s+', ' ', text)
            else:
                text = text.replace('\r\n', '\n')
            HTMLTemplate('@text', self.index, parent=self.current, text=text)

    def visitRawText(self, ctx: PMLParser.RawTextContext):
        text = ctx.getText()
        if text.strip('\uFEFF'):
            tag_name = self.current.tag_name
            if tag_name == '@python':
                line_no = ctx.start.line
                text = '#\n' * (line_no - 1) + text
            self.current.text = text

    def visitRawTag(self, ctx: PMLParser.RawTagContext):
        tag_name = '@' + ctx.getText().strip()[1:]
        self.current = HTMLTemplate(tag_name, self.index, parent=self.current)
        self.current.filename = self.root.filename
        # raw nodes goes first
        self.current.parent.children.insert(0, self.current.parent.children.pop())

    def visitRawCloseTag(self, ctx: PMLParser.RawCloseTagContext):
        self.current = self.current.parent

    def visitTagBegin(self, ctx: PMLParser.TagBeginContext):
        tag_name = ctx.children[1].getText()
        if tag_name in SPECIAL_ELEMENTS:
            tag_name = '@' + tag_name
        self.current = HTMLTemplate(tag_name, self.index, parent=self.current)
        # if not self.root: self.root = self.current
        self.visitChildren(ctx)
        if ctx.children[-1].symbol.type == PMLLexer.SLASH_CLOSE or self.current.tag_name.lower() in VOID_ELEMENTS:
            self.current = self.current.parent

    def visitAttrName(self, ctx: PMLParser.AttrNameContext):
        self.cur_attr = ctx.getText()
        if self.cur_attr != 'class':
            self.current.set_attr(self.cur_attr, None)

    def visitAttrValue(self, ctx: PMLParser.AttrValueContext):
        text = ctx.getText().strip('"\'')
        if text == '{}':
            value = '{}'
        elif (text.startswith('{') or text.startswith('!{')) and text.endswith('}'):
            reactive = text[0] == '{'
            text = text[text.index('{') + 1:-1]
            if not self.cur_attr.startswith('set:'):
                value = MacroCode(reactive, compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)
            else:
                text = f"({text} or '')"
                value = MacroCode(reactive, compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)
        elif FORMATTED_EXPRESSION.search(text):
            reactive = '`!{' in text or ' !{' in text
            text = text.replace('!{', '{').replace('`{', '{').replace('}`', '}')
            value = MacroCode(reactive, compile(f'f"{text}"', f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)
        else:
            value = text
        self.current.set_attr(self.cur_attr, value)

    def visitRawName(self, ctx:PMLParser.RawNameContext):
        self.cur_attr = ctx.getText()
        self.current.attributes[self.cur_attr] = None

    def visitRawValue(self, ctx:PMLParser.RawValueContext):
        self.current.attributes[self.cur_attr] = ctx.getText().strip('"\'')

    def visitTagEnd(self, ctx: PMLParser.TagEndContext):
        tag_name = ctx.children[1].getText()
        if tag_name in SPECIAL_ELEMENTS:
            tag_name = '@' + tag_name
        while self.current:
            if tag_name == self.current.tag_name:
                break
            self.current = self.current.parent
        else:
            raise IllegalStateException(f"close tag don't match {tag_name}")
        self.current = self.current.parent

    def visitMacroBegin(self, ctx: PMLParser.MacroCommandContext):
        reactive = ctx.children[0].getText().startswith('!')
        command = ctx.children[1].getText()

        macro_chunks = re.search(r"^(\w+)\s+(.*)$", command)
        macro = None
        if not macro_chunks:
            tag_name = command.strip()
            text = ''
        else:
            tag_name = macro_chunks.group(1).strip()
            text = macro_chunks.group(2).strip()
            if tag_name not in ('for', 'set'):
                macro = MacroCode(reactive, compile(text, f"<{tag_name}>", "eval"), text)

        # gen 'if' subtree
        if tag_name == 'if':
            parent = HTMLTemplate('#if', self.index, self.current)
            self.current = HTMLTemplate('#choice', self.index, parent=parent)
            self.current.macro = macro
        elif tag_name == 'for':
            parent = HTMLTemplate('#for', self.index, self.current)
            sides = text.split('#')
            chunks = sides[0].split(' in ')
            var_name = chunks[0].strip()
            iterator = compile(chunks[1], f"<{parent.path()}:iterator>", "eval")
            index_func = compile(sides[1], f"<{parent.path()}:index_func>", "eval") if len(sides) > 1 else None

            self.current = HTMLTemplate('#loop', self.index, parent=parent)
            self.current.macro = [MacroCode(reactive, iterator, sides[0]), MacroCode(reactive, index_func, sides[1] if len(sides)>1 else None)]
            self.current.text = var_name
        elif tag_name == 'elif':
            self.current = HTMLTemplate('#choice', self.index, parent=self.current.parent)
            self.current.macro = macro
        elif tag_name == 'else':
            self.current = HTMLTemplate('#else', self.index, parent=self.current.parent)
        elif tag_name == 'set':
            self.current = HTMLTemplate('#set', self.index, parent=self.current)
            chunks = text.split(':=')
            if len(chunks) != 2:
                raise IllegalStateException("set command should contains `:=` marker")
            var_name = chunks[0].strip()
            expr = compile(chunks[1].strip(), f"<{self.current.path()}>", "eval")
            self.current.macro = MacroCode(reactive, expr, chunks[1].strip())
            self.current.text = var_name

    def visitMacroEnd(self, ctx: PMLParser.MacroEndContext):
        macro_tag = '#'+ctx.children[1].getText().strip()
        while self.current:
            if macro_tag == self.current.tag_name:
                break
            self.current = self.current.parent
        else:
            raise IllegalStateException(f"macro close tag don't match {macro_tag}")
        self.current = self.current.parent

    def visitInlineMacro(self, ctx: PMLParser.InlineMacroContext):
        macro = HTMLTemplate('@macro', self.index, parent=self.current)
        text = ctx.children[1].getText()
        code = compile(text, f'<{self.current}:macro>', 'eval')
        macro.macro = MacroCode(ctx.children[0].getText().startswith('!'), code, text)

    def visitErrorNode(self, node):
        raise IllegalStateException(f'wrong node {node.getText()}')


class ErrorVisitor(ErrorListener):
    def __init__(self, filename, error_callback):
        super().__init__()
        self.filename = filename
        self.error_callback = error_callback

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.error_callback(f"{self.filename}: line {line}:{column} {msg}")


def load(filename: Path, error_callback: typing.Callable[[str], None]) -> typing.Optional[HTMLTemplate]:
    in_stream = FileStream(str(filename), encoding='utf-8')
    lexer = PMLLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = PMLParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorVisitor(filename, error_callback))
    tree = parser.process()

    visitor = HTMLVisitor(filename)
    try:
        visitor.visit(tree)
    except IllegalStateException as e:
        error_callback(f'{filename}> {e}')
        return None
    except SyntaxError as e:
        error_callback(f'{filename}> {e} column:{e.args[1][2]} {{{e.args[1][3]}}}')
        return None

    # find external code file
    code_filename = filename.with_suffix('.py')
    if code_filename.exists():
        HTMLTemplate("@python", 0, visitor.root, text=code_filename.read_text(encoding='utf-8'))
        # raw nodes goes first
        visitor.root.children.insert(0, visitor.root.children.pop())

    res: HTMLTemplate = visitor.root
    res.hex_digest = hashlib.md5(Path(filename).read_bytes()).hexdigest()
    return res


def _search_component(path: Path, name: str) -> Path | None:
    for file in path.glob(f"**/{name}.html"):
        return file
    return None


def collect_template(session: Session, name: str) -> typing.Optional[HTMLTemplate]:
    global templates

    key = session.app +  '/' + name
    if key in templates:
        return templates[key]

    path = _search_component(session.app_path, name)
    if not path:
        if name in templates:
            templates[key] = templates[name]
            return templates[name]
        #elif config.PRODUCTIVE:
        #    templates[key] = None
        #    return None

        path = _search_component(config.COMPONENTS_PATH, name)
        if not path:
            if not config.PRODUCTIVE:
                session.error(f'component {name} not found')
            templates[key] = None
            return None
        key = name

    template = load(path, session.error)
    if template:
        template.name = name
        templates[key] = template
    return template


def get_static_url(app: str, template_file_name: Path, sub_dir: str | None, file_name: str) -> str:
    try:
        return get_static_url_cached(app, template_file_name, sub_dir, file_name)
    except FileNotFoundError:
        return '#'

@lru_cache(maxsize=1000)
def get_static_url_cached(app: str, template_file_name: Path, sub_dir: str | None, file_name: str) -> str:
    if sub_dir and sub_dir in config.ALLOWED_DIRS:
        path = config.ALLOWED_DIRS[sub_dir] / file_name
        if path.exists():
            return config.WEB_PATH + '/'.join(['', '$' + sub_dir, '~', file_name])
        else:
            raise FileNotFoundError(file_name)

    # omit 'static' part
    if sub_dir and sub_dir != config.STATIC_DIR:
        search_name = config.STATIC_DIR + '/' + sub_dir + '/' + file_name
        web_name = sub_dir + '/' + file_name
    else:
        search_name = config.STATIC_DIR + '/' + file_name
        web_name = file_name

    # check relative to component
    path = template_file_name.parent / search_name
    if path.exists():
        return config.WEB_PATH + '/'.join(['', template_file_name.name, '~', web_name])
    else:
        # relative to app
        path = config.APPS_PATH / app / search_name
        if path.exists():
            return config.WEB_PATH + '/'.join(['', app, '~', web_name])
        else:
            # relative to components base
            path = config.COMPONENTS_PATH / search_name
            if path.exists():
                return config.WEB_PATH + '/'.join(['', '~', web_name])
            else:
                raise FileNotFoundError(search_name)


class StyleVisitor(PMLParserVisitor):
    parser = cssutils.CSSParser(validate=False, raiseExceptions=True)

    def __init__(self, app:str, class_name: str, template_name: Path):
        self.app = app
        self.class_name = class_name
        self.template_name = template_name
        self.styles: typing.List[str] = []
        self.in_style = False
        self.global_mode = False

    def visitRawText(self, ctx: PMLParser.RawTextContext):
        if not self.in_style:
            return

        def static(file_name) -> str:
            return f'url("{get_static_url(self.app, self.template_name, None, file_name)}")'

        text = ctx.getText()
        text = '\n' * (ctx.start.line-1) + text
        text = sass.compile(string=text, output_style='compact', include_paths=[str(config.CSS_PATH)], custom_functions=[
            sass.SassFunction("static", ("$url", ), static)
        ])

        if self.global_mode:
            self.styles.append(text)
        else:
            # color any selector and sub-selector with component-based class
            base_class = f'.{self.class_name}'

            # collect and cut all global marks to make css parser happy
            global_marks = []
            glo = ':global('

            def parse_globals(text: str):
                res = []
                for line, s in enumerate(text.splitlines()):
                    while glo in s:
                        pos = s.index(glo)
                        left = pos + len(glo)
                        right = left
                        cnt = 1
                        while cnt > 0 and right < len(s):
                            if s[right] == ')':
                                cnt -= 1
                            elif s[right] == '(':
                                cnt += 1
                            elif s[right] == '{':
                                break
                            right += 1
                        if cnt > 0:
                            raise ValueError(':global pseudo-class should be closed')
                        global_marks.append((line + 1, left + 1))
                        s = s[:pos] + ' ' * len(glo) + s[left:right - 1] + ' ' + s[right:]
                    res.append(s)
                return '\n'.join(res)

            text = parse_globals(text)

            # walk parse tree and inject base class
            def go(l):
                for node in l:
                    if type(node) == CSSMediaRule:
                        go(node.cssRules)
                    elif type(node) == CSSStyleRule:
                        for sel in node.selectorList:
                            lst = sel.seq
                            marked = False
                            i = 0
                            while i < len(lst):
                                token = lst[i]

                                def mark(shift: int, after: int):
                                    nonlocal i, marked
                                    if (token.line, token.col - shift) not in global_marks:
                                        lst.insert(i + after, base_class, 'class')
                                        i += 1
                                    marked = True

                                if not marked:
                                    if token.type in ('type-selector', 'universal'):  # a, *
                                        mark(0, 1)
                                    elif token.type in ('class', 'id', 'pseudo-class'):  # .Table, #id, :not
                                        mark(1, 0)
                                    elif token.type == 'pseudo-element':  # ::selection
                                        mark(2, 0)
                                    elif token.type == 'attribute-start':  # [...]
                                        mark(0, 0)
                                elif token.type in ('descendant', 'child', 'adjacent-sibling', 'following-sibling'):  # ' ', >, +, ~
                                    marked = False
                                i += 1

            sheet = self.parser.parseString(text)
            go(sheet)

            # first naive attempt, saved for history
            # chunks = re.split(r'(?<=})', text)
            # res = '\n'.join(f'.{self.class_name} {chunk.strip()}' for chunk in chunks if chunk.strip())

            # recover css text with injections
            self.styles.append(str(sheet.cssText, 'utf8'))

    def visitRawName(self, ctx: PMLParser.RawNameContext):
        name = ctx.getText()
        if name == 'global':
            self.global_mode = True

    def visitRawTag(self, ctx: PMLParser.RawTagContext):
        if ctx.getText().strip()[1:] == 'style':
            self.in_style = True
            self.global_mode = False

    def visitRawCloseTag(self, ctx: PMLParser.RawCloseTagContext):
        self.in_style = False

    def visitErrorNode(self, node):
        raise IllegalStateException(f'wrong node {node.getText()}')


def load_styles(app:str, name: str, filename: Path):
    in_stream = FileStream(str(filename), encoding='utf-8')
    lexer = PMLLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = PMLParser(stream)
    tree = parser.process()

    visitor = StyleVisitor(app, name, filename)
    visitor.visit(tree)
    return '\n'.join(visitor.styles)


def collect_styles(app:str, app_path: Path, error_callback: typing.Callable[[str], None]) -> str:
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

