from __future__ import annotations

import os
import re
import typing
import traceback

import cssutils
import sass
from antlr4 import FileStream, CommonTokenStream, IllegalStateException
from antlr4.error.ErrorListener import ErrorListener
from pantra.common import UniNode, ADict
from cssutils.css import CSSMediaRule, CSSStyleRule

from .grammar.PMLLexer import PMLLexer
from .grammar.PMLParser import PMLParser
from .grammar.PMLParserVisitor import PMLParserVisitor

from pantra.defaults import CSS_PATH, COMPONENTS_PATH

if typing.TYPE_CHECKING:
    from pantra.session import Session
    from typing import *
    from types import CodeType

__all__ = ['HTMLTemplate', 'collect_styles', 'collect_template']

VOID_ELEMENTS = 'area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr'.split('|')
SPECIAL_ELEMENTS = 'slot|event|scope|react|component|'.split('|')

templates: typing.Dict[str, HTMLTemplate] = {}


class HTMLTemplate(UniNode):
    code_base: Dict[str, CodeType] = {}
    __slots__ = ('tag_name', 'attributes', 'text', 'macro', 'name', 'filename', 'code')

    def __init__(self, tag_name: str, parent: Optional['HTMLTemplate'] = None, attributes: Optional[List[Union[Dict, ADict]]] = None, text: str = None):
        super().__init__(parent)
        self.tag_name: str = tag_name
        self.attributes: Dict[str, Union[str, CodeType]] = attributes and ADict(attributes) or ADict()
        self.text: str = text
        self.macro: CodeType = None
        self.name: Optional[str] = None
        self.filename: Optional[str] = None
        self.code: Optional[Union[CodeType, str]] = None

    def __str__(self):
        return self.tag_name


class MyVisitor(PMLParserVisitor):

    def __init__(self, filename: str):
        name = os.path.splitext(os.path.basename(filename))[0]
        root = HTMLTemplate(f'${name}')
        root.filename = filename
        self.root: typing.Optional[HTMLTemplate] = root
        self.current: typing.Optional[HTMLTemplate] = root
        self.cur_attr: typing.Optional[str] = None

    def visitText(self, ctx: PMLParser.TextContext):
        text = ctx.getText().strip().strip('\uFEFF')
        if text and self.current != self.root:
            HTMLTemplate('@text', parent=self.current, text=text)

    def visitRawText(self, ctx: PMLParser.RawTextContext):
        text = ctx.getText()
        if text.strip().strip('\uFEFF'):
            tag_name = self.current.tag_name
            if tag_name == '@python':
                line_no = ctx.start.line
                text = '#\n' * (line_no - 1) + text
            self.current.text = text

    def visitRawTag(self, ctx: PMLParser.RawTagContext):
        tag_name = '@' + ctx.getText().strip()[1:]
        self.current = HTMLTemplate(tag_name, parent=self.current)
        self.current.filename = self.root.filename
        # raw nodes goes first
        self.current.parent.children.insert(0, self.current.parent.children.pop())

    def visitRawCloseTag(self, ctx: PMLParser.RawCloseTagContext):
        self.current = self.current.parent

    def visitTagBegin(self, ctx: PMLParser.TagBeginContext):
        tag_name = ctx.children[1].getText()
        if tag_name in SPECIAL_ELEMENTS:
            tag_name = '@' + tag_name
        self.current = HTMLTemplate(tag_name=tag_name, parent=self.current)
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
            if text.startswith('{'):
                if not self.cur_attr.startswith('set:'):
                    value = compile(text.strip('{}'), f'<attribute:{self.cur_attr}>', 'eval')
                else:
                    text = text.strip('{}')
                    text = f"({text} or '')"
                    value = compile(text, f'<attribute:{self.cur_attr}>', 'eval')
            else:
                value = compile(f'f"{text}"', f'<attribute:{self.cur_attr}>', 'eval')
        else:
            value = text
        self.current.attributes[self.cur_attr] = value

    def visitRawName(self, ctx:PMLParser.RawNameContext):
        self.cur_attr = ctx.getText()
        self.current.attributes[self.cur_attr] = None

    def visitRawValue(self, ctx:PMLParser.RawValueContext):
        self.current.attributes[self.cur_attr] = ctx.getText()

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

    def visitMacroCommand(self, ctx: PMLParser.MacroCommandContext):
        command = ctx.getText()

        macro_chunks = re.search(r"^(\w+)\s+(.*)$", command)
        if not macro_chunks:
            tag_name = command.strip()
            macro = ''
        else:
            tag_name = macro_chunks.group(1).strip()
            macro = macro_chunks.group(2).strip()

        # gen 'if' subtree
        if tag_name == 'if':
            parent = HTMLTemplate('#if', self.current)
            self.current = HTMLTemplate('#choice', parent=parent)
            self.current.macro = macro or "True"
        elif tag_name == 'for':
            parent = HTMLTemplate('#for', self.current)
            parent.macro = macro
            self.current = HTMLTemplate('#loop', parent=parent)
        elif tag_name == 'elif':
            self.current = HTMLTemplate('#choice', parent=self.current.parent)
            self.current.macro = macro or "True"
        elif tag_name == 'else':
            self.current = HTMLTemplate('#else', parent=self.current.parent)
        elif tag_name == 'set':
            self.current = HTMLTemplate('#set', parent=self.current)
            self.current.macro = macro

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
        macro = HTMLTemplate('@macro', parent=self.current)
        text = ctx.children[1].getText()
        code = compile(text, '<macro>', 'eval')
        macro.macro = code

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

    visitor = MyVisitor(filename)
    try:
        visitor.visit(tree)
    except IllegalStateException as e:
        error_callback(f'{filename}> {e}')
        return None
    except SyntaxError as e:
        error_callback(f'{filename}> {e}')
        return None
    return visitor.root


def _search_component(path, name):
    for root, dirs, files in os.walk(path):
        for file in files:  # type: str
            if file.endswith('html'):
                if os.path.basename(file) == f'{name}.html':
                    return os.path.join(root, file)
    return None


def collect_template(session: Session, name) -> typing.Optional[HTMLTemplate]:
    global templates

    key = '/'.join([session.app_path, name])
    if key in templates:
        return templates[key]

    path = _search_component(session.app_path, name)
    if not path:
        path = _search_component(COMPONENTS_PATH, name)
        if not path:
            # session.error(f'component {name} not found')
            return None

    template = load(path, session.error)
    if template:
        template.name = name
        templates[key] = template
    return template


class StyleVisitor(PMLParserVisitor):
    parser = cssutils.CSSParser(validate=False, raiseExceptions=True)

    def __init__(self, class_name: str):
        self.class_name = class_name
        self.styles: typing.List[str] = []
        self.in_style = False
        self.global_mode = False

    def visitRawText(self, ctx: PMLParser.RawTextContext):
        if not self.in_style:
            return

        text = ctx.getText()
        text = '\n' * (ctx.start.line-1) + text
        text = sass.compile(string=text, output_style='compact', include_paths=[CSS_PATH])

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


def load_styles(name: str, filename: str):
    in_stream = FileStream(filename, encoding='utf-8')
    lexer = PMLLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = PMLParser(stream)
    tree = parser.process()

    visitor = StyleVisitor(name)
    visitor.visit(tree)
    return '\n'.join(visitor.styles)


def collect_styles(app_path, error_callback: typing.Callable[[str], None]) -> str:
    styles = []
    for root, dirs, files in os.walk(app_path):
        for file in files:  # type: str
            if file.endswith('html'):
                name, ext = os.path.splitext(file)
                path = os.path.join(root, file)
                try:
                    res = load_styles(name, path)
                except Exception as e:
                    error_callback(f'{path}> Style collector> {e}')
                else:
                    if res:
                        styles.append(res)

    return '\n'.join(styles)

