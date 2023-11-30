from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
import re
import typing

import cssutils
import sass
from antlr4 import FileStream, CommonTokenStream, IllegalStateException
from antlr4.error.ErrorListener import ErrorListener
from cssutils.css import CSSMediaRule, CSSStyleRule

from .grammar.PMLLexer import PMLLexer
from .grammar.PMLParser import PMLParser
from .grammar.PMLParserVisitor import PMLParserVisitor

from pantra.common import UniNode, ADict
from pantra.settings import config

if typing.TYPE_CHECKING:
    from pantra.session import Session
    from typing import *
    from types import CodeType

__all__ = ['MacroCode', 'HTMLTemplate', 'collect_styles', 'collect_template', 'get_static_url']

VOID_ELEMENTS = 'area base br col embed hr img input link meta param source track wbr'.split()
SPECIAL_ELEMENTS = 'slot event scope react component '.split()

templates: typing.Dict[str, HTMLTemplate] = {}


class MacroCode(typing.NamedTuple):
    reactive: bool
    code: CodeType | None


class HTMLTemplate(UniNode):
    code_base: Dict[str, CodeType] = {}
    __slots__ = ('tag_name', 'attributes', 'text', 'macro', 'name', 'filename', 'code', 'index', 'hex_digest')

    def __init__(self, tag_name: str, index: int, parent: Optional['HTMLTemplate'] = None, attributes: Optional[Union[Dict, ADict]] = None, text: str = None):
        super().__init__(parent)
        self.tag_name: str = tag_name
        self.attributes: Dict[str, str | MacroCode | None] = attributes and ADict(attributes) or ADict()
        self.text: str = text
        self.macro: MacroCode | list[MacroCode] | None = None
        self.name: Optional[str] = None
        self.filename: Optional[str] = None
        self.code: Optional[Union[CodeType, str]] = None
        self.index: int = index
        self.hex_digest: str = ''

    def __str__(self):
        return self.tag_name


class HTMLVisitor(PMLParserVisitor):

    def __init__(self, filename: str):
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
        text = ctx.getText().strip('\uFEFF').replace('\r\n', '\n')
        if text.strip() and self.current != self.root:
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
            self.current.attributes[self.cur_attr] = None

    def visitAttrValue(self, ctx: PMLParser.AttrValueContext):
        text = ctx.getText().strip('"\'')
        if '{' in text:
            reactive = False
            if text.startswith('!{'):
                reactive = True
                text = text[1:]
            if text.startswith('{'):
                text = text.strip('{}')
                if not self.cur_attr.startswith('set:'):
                    value = MacroCode(reactive, compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'))
                else:
                    text = f"({text} or '')"
                    value = MacroCode(reactive, compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'))
            else:
                reactive = '`!{' in text
                text = text.replace('`{', '{').replace('`!{', '{').replace('}`', '}')
                value = MacroCode(reactive, compile(f'f"{text}"', f'<{self.current.path()}:{self.cur_attr}>', 'eval'))
        else:
            value = text
        self.current.attributes[self.cur_attr] = value

    def visitRawName(self, ctx:PMLParser.RawNameContext):
        self.cur_attr = ctx.getText()
        self.current.attributes[self.cur_attr] = None

    def visitRawValue(self, ctx:PMLParser.RawValueContext):
        self.current.attributes[self.cur_attr] = ctx.getText().strip('"\'')

    def visitTagEnd(self, ctx: PMLParser.TagEndContext):
        tag_name = ctx.children[1].getText()
        if tag_name in SPECIAL_ELEMENTS:
            tag_name = '@' + tag_name
        match = False
        while self.current:
            if tag_name == self.current.tag_name:
                match = True
                break
            self.current = self.current.parent
        if not match:
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
                macro = MacroCode(reactive, compile(text, f"<{tag_name}>", "eval"))

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

            parent.macro = [MacroCode(reactive, iterator), MacroCode(reactive, index_func)]
            parent.text = var_name
            self.current = HTMLTemplate('#loop', self.index, parent=parent)
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
            self.current.macro = MacroCode(reactive, expr)
            self.current.text = var_name

    def visitMacroEnd(self, ctx: PMLParser.MacroEndContext):
        macro_tag = '#'+ctx.children[1].getText().strip()
        match = False
        while self.current:
            if macro_tag == self.current.tag_name:
                match = True
                break
            self.current = self.current.parent
        if not match:
            raise IllegalStateException(f"macro close tag don't match {macro_tag}")
        self.current = self.current.parent

    def visitInlineMacro(self, ctx: PMLParser.InlineMacroContext):
        macro = HTMLTemplate('@macro', self.index, parent=self.current)
        text = ctx.children[1].getText()
        code = compile(text, f'<{self.current}:macro>', 'eval')
        macro.macro = MacroCode(ctx.children[0].getText().startswith('!'), code)

    def visitErrorNode(self, node):
        raise IllegalStateException(f'wrong node {node.getText()}')


class ErrorVisitor(ErrorListener):
    def __init__(self, filename, error_callback):
        super().__init__()
        self.filename = filename
        self.error_callback = error_callback

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.error_callback(f"{self.filename}: line {line}:{column} {msg}")


def load(filename: str, error_callback: typing.Callable[[str], None]) -> typing.Optional[HTMLTemplate]:
    in_stream = FileStream(filename, encoding='utf-8')
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
        error_callback(f'{filename}> {e}')
        return None

    # find external code file
    code_filename = filename + '.py'
    if (f:=Path(code_filename)).exists():
        HTMLTemplate("@python", visitor.root, text=f.read_text(encoding='utf-8'))
        # raw nodes goes first
        visitor.root.children.insert(0, visitor.root.children.pop())

    res: HTMLTemplate = visitor.root
    res.hex_digest = hashlib.md5(Path(filename).read_bytes()).hexdigest()
    return res


def _search_component(path: Path, name: str) -> str | None:
    for file in path.glob(f"**/{name}.html"):
        return str(file)
    return None


def collect_template(session: Session, name: str) -> typing.Optional[HTMLTemplate]:
    global templates

    key = session.app +  '/' + name
    if key in templates:
        return templates[key]

    path = _search_component(session.app_path, name)
    if not path:
        path = _search_component(config.COMPONENTS_PATH, name)
        if not path:
            # session.error(f'component {name} not found')
            return None

    template = load(path, session.error)
    if template:
        template.name = name
        templates[key] = template
    return template


@lru_cache(maxsize=1000)
def get_static_url(app: str, template_file_name: Path, file_name: str):
    if file_name.startswith(config.STATIC_DIR + '/'):
        file_name = file_name[len(config.STATIC_DIR) + 1:]

    # check relative to component
    path = template_file_name.parent / config.STATIC_DIR / file_name
    if path.exists():
        return '/'.join(['', template_file_name.name, '~', file_name])
    else:
        # relative to app
        path = config.APPS_PATH / app / config.STATIC_DIR / file_name
        if path.exists():
            return '/'.join(['', app, '~', file_name])
        else:
            # relative to components base
            path = config.COMPONENTS_PATH / config.STATIC_DIR / file_name
            if path.exists():
                return '/'.join(['', '~', file_name])
            else:
                raise FileExistsError(file_name)


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
            return f'url("{get_static_url(self.app, self.template_name, file_name)}")'

        text = ctx.getText()
        text = '\n' * (ctx.start.line-1) + text
        text = sass.compile(string=text, output_style='compact', include_paths=[str(config.CSS_PATH)], custom_functions=[
            sass.SassFunction("static", ("$a", ), static)
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

