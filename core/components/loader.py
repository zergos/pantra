import os
import re
import typing

import cssutils
import sass
from antlr4.error.ErrorListener import ErrorListener
from attrdict import AttrDict
from cssutils.css import CSSMediaRule, CSSStyleRule

from .htmlnode import HTMLTemplate

from antlr4 import *
from .grammar.BCDLexer import BCDLexer
from .grammar.BCDParser import BCDParser
from .grammar.BCDParserVisitor import BCDParserVisitor

from logging import getLogger

from ..common import DynamicClasses
from ..defaults import BASE_PATH, CSS_PATH

logger = getLogger(__name__)

VOID_ELEMENTS = 'area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr'.split('|')


class MyVisitor(BCDParserVisitor):

    def __init__(self, filename: str):
        name = os.path.splitext(os.path.basename(filename))[0]
        root = HTMLTemplate(f'in{name}')
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
        self.current.parent._NodeMixin__children_.insert(0, self.current.parent._NodeMixin__children_.pop())

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

    def visitMacroBegin(self, ctx: BCDParser.MacroBeginContext):
        self.current = HTMLTemplate("#condition", parent=self.current)
        self.visitChildren(ctx)

    def visitMacroCommand(self, ctx: BCDParser.MacroCommandContext):
        command = ctx.getText()
        macro_chunks = re.search(r"^(\w+)\s+(.*)$", command)
        self.current.tag_name = '#' + macro_chunks.group(1).strip()
        self.current.macro = macro_chunks.group(2).strip()

        # gen 'if' subtree
        if self.current.tag_name == '#if':
            self.current = HTMLTemplate('#choice', parent=self.current)
            self.current.macro = self.current.parent.macro
        elif self.current.tag_name == '#elif':
            self.current.tag_name = '#choice'


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
        logger.error(f'{self.root.name}> {node.getText()}')


class ErrorVisitor(ErrorListener):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        logger.error(f"{self.filename}: line {line}:{column} {msg}")

    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        pass

    def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex, conflictingAlts, configs):
        # logger.error(f"{self.filename}: full context {startIndex}:{stopIndex} {conflictingAlts!r}")
        pass

    def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
        pass


def load(filename: str):
    in_stream = FileStream(filename, encoding='utf-8')
    lexer = BCDLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = BCDParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorVisitor(filename))
    tree = parser.process()

    visitor = MyVisitor(filename)
    visitor.visit(tree)
    return visitor.root


class StyleVisitor(BCDParserVisitor):

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

            parser = cssutils.CSSParser(validate=False)
            lst = parser.parseString(text)
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


def load_styles(name: str, filename: str):
    in_stream = FileStream(filename, encoding='utf-8')
    lexer = BCDLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = BCDParser(stream)
    tree = parser.process()

    visitor = StyleVisitor(name)
    visitor.visit(tree)
    return '\n'.join(visitor.styles)
