from __future__ import annotations

import os
import re
import typing

import cssutils
import sass
from antlr4.error.ErrorListener import ErrorListener
from cssutils.css import CSSMediaRule, CSSStyleRule

from .htmlnode import HTMLTemplate

from antlr4 import *
from .grammar.BCDLexer import BCDLexer
from .grammar.BCDParser import BCDParser
from .grammar.BCDParserVisitor import BCDParserVisitor

from core.defaults import CSS_PATH, COMPONENTS_PATH

if typing.TYPE_CHECKING:
    from core.session import Session

__all__ = ['collect_styles', 'collect_template']

VOID_ELEMENTS = 'area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr'.split('|')

templates: typing.Dict[str, HTMLTemplate] = {}


class MyVisitor(BCDParserVisitor):

    def __init__(self, filename: str):
        name = os.path.splitext(os.path.basename(filename))[0]
        root = HTMLTemplate(f'${name}')
        root.filename = filename
        self.root: typing.Optional[HTMLTemplate] = root
        self.current: typing.Optional[HTMLTemplate] = root
        self.cur_attr: typing.Optional[str] = None

    def visitText(self, ctx: BCDParser.TextContext):
        text = ctx.getText().strip().strip('\uFEFF')
        if text:
            HTMLTemplate('@text', parent=self.current, text=text)

    def visitRawText(self, ctx: BCDParser.RawTextContext):
        text = ctx.getText()
        if text.strip().strip('\uFEFF'):
            tag_name = self.current.tag_name
            if tag_name == 'python':
                line_no = ctx.start.line
                text = '#\n' * (line_no - 1) + text
                self.current.filename = self.root.filename
            self.current.text = text

    def visitRawTag(self, ctx: BCDParser.RawTagContext):
        text = ctx.getText().strip()
        self.current = HTMLTemplate(text[1:], parent=self.current)
        # raw nodes goes first
        self.current.parent.children.insert(0, self.current.parent.children.pop())

    def visitRawCloseTag(self, ctx: BCDParser.RawCloseTagContext):
        self.current = self.current.parent

    def visitTagBegin(self, ctx: BCDParser.TagBeginContext):
        self.current = HTMLTemplate(tag_name=ctx.children[1].getText(), parent=self.current)
        # if not self.root: self.root = self.current
        self.visitChildren(ctx)
        if ctx.children[-1].symbol.type == BCDLexer.SLASH_CLOSE or self.current.tag_name.lower() in VOID_ELEMENTS:
            self.current = self.current.parent

    def visitAttrName(self, ctx: BCDParser.AttrNameContext):
        self.cur_attr = ctx.getText()
        if self.cur_attr != 'class':
            self.current.attributes[self.cur_attr] = None

    def visitAttrValue(self, ctx: BCDParser.AttrValueContext):
        if self.cur_attr == 'class':
            self.current.classes = ctx.getText().strip()
        else:
            self.current.attributes[self.cur_attr] = ctx.getText()

    def visitTagEnd(self, ctx: BCDParser.TagEndContext):
        tag_name = ctx.children[1].getText()
        match = False
        while self.current:
            if tag_name == self.current.tag_name:
                match = True
                break
            self.current = self.current.parent
        if not match:
            raise IllegalStateException(f"close tag don't match {tag_name}")
        self.current = self.current.parent

    def visitMacroCommand(self, ctx: BCDParser.MacroCommandContext):
        command = ctx.getText()

        macro_chunks = re.search(r"^(\w+)\s+(.*)$", command)
        if not macro_chunks:
            tag_name = '#' + command.strip()
            macro = ''
        else:
            tag_name = '#' + macro_chunks.group(1).strip()
            macro = macro_chunks.group(2).strip()

        # gen 'if' subtree
        if tag_name == '#if':
            parent = HTMLTemplate('#if', self.current)
            self.current = HTMLTemplate('#choice', parent=parent)
            self.current.macro = macro or "True"
        elif tag_name == '#for':
            parent = HTMLTemplate('#for', self.current)
            parent.macro = macro
            self.current = HTMLTemplate('#loop', parent=parent)
        elif tag_name == '#elif':
            self.current = HTMLTemplate('#choice', parent=self.current.parent)
            self.current.macro = macro or "True"
        elif tag_name == '#else':
            self.current = HTMLTemplate('#else', parent=self.current.parent)

    def visitMacroEnd(self, ctx: BCDParser.MacroEndContext):
        macro_tag = '#'+ctx.children[1].getText().strip()
        match = False
        while self.current:
            if macro_tag == self.current.tag_name:
                match = True
                break
            self.current = self.current.parent
        if not match:
            raise IllegalStateException(f"{self.root.filename}> macro close tag don't match {macro_tag}")
        self.current = self.current.parent

    def visitInlineMacro(self, ctx: BCDParser.InlineMacroContext):
        macro = HTMLTemplate('macro', parent=self.current)
        macro.macro = ctx.children[1].getText()

    def visitErrorNode(self, node):
        raise IllegalStateException(f'{self.root.filename}> wrong node {node.getText()}')


class ErrorVisitor(ErrorListener):
    def __init__(self, filename, error_callback):
        super().__init__()
        self.filename = filename
        self.error_callback = error_callback

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.error_callback(f"{self.filename}: line {line}:{column} {msg}")


def load(filename: str, error_callback: typing.Callable[[str], None]) -> typing.Optional[HTMLTemplate]:
    in_stream = FileStream(filename, encoding='utf-8')
    lexer = BCDLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = BCDParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorVisitor(filename, error_callback))
    tree = parser.process()

    visitor = MyVisitor(filename)
    try:
        visitor.visit(tree)
    except IllegalStateException as e:
        error_callback(str(e))
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

    key = '/'.join([session.app, name])
    if key in templates:
        return templates[key]

    path = _search_component(session.app, name)
    if not path:
        path = _search_component(COMPONENTS_PATH, name)
        if not path:
            session.error(f'component {name} not found')
            return None

    template = load(path, session.error)
    if template:
        template.name = name
        templates[key] = template
    return template


class StyleVisitor(BCDParserVisitor):
    parser = cssutils.CSSParser(validate=False, raiseExceptions=True)

    def __init__(self, class_name: str):
        self.class_name = class_name
        self.styles: typing.List[str] = []
        self.in_style = False
        self.global_mode = False

    def visitRawText(self, ctx: BCDParser.RawTextContext):
        if not self.in_style:
            return

        text = ctx.getText()
        text = sass.compile(string=text, output_style='compact', include_paths=[CSS_PATH])

        if self.global_mode:
            self.styles.append(text)
        else:
            base_class = f'.ctx-{self.class_name}'

            def go(l):
                res = []
                for node in l:
                    if type(node) == CSSMediaRule:
                        res.append(f'{node.atkeyword} {node.media.mediaText} {{\n{go(node.cssRules)}\n}}')
                    elif type(node) == CSSStyleRule:
                        s = f'{base_class} ' + f', {base_class} '.join(seq.selectorText for seq in node.selectorList.seq)
                        css_text = node.style.cssText.replace("\n", " ")
                        res.append(f'{s} {{ {css_text} }}')
                return '\n'.join(res)

            lst = self.parser.parseString(text)
            res = go(lst)

            # chunks = re.split(r'(?<=})', text)
            # res = '\n'.join(f'.ctx-{self.class_name} {chunk.strip()}' for chunk in chunks if chunk.strip())
            self.styles.append(res)

    def visitRawName(self, ctx: BCDParser.RawNameContext):
        name = ctx.getText()
        if name == 'global':
            self.global_mode = True

    def visitRawTag(self, ctx: BCDParser.RawTagContext):
        if ctx.getText().strip()[1:] == 'style':
            self.in_style = True
            self.global_mode = False

    def visitRawCloseTag(self, ctx: BCDParser.RawCloseTagContext):
        self.in_style = False

    def visitErrorNode(self, node):
        raise IllegalStateException(f'wrong node {node.getText()}')


def load_styles(name: str, filename: str):
    in_stream = FileStream(filename, encoding='utf-8')
    lexer = BCDLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = BCDParser(stream)
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
                    error_callback(f'{path}> {e}')
                else:
                    if res:
                        styles.append(res)

    return '\n'.join(styles)

