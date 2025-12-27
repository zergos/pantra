from __future__ import annotations

import hashlib
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

from pantra.settings import config
from .template import HTMLTemplate, MacroCode
from .static import get_static_url

__all__ = ['load', 'load_styles']

VOID_ELEMENTS = 'area base br col embed hr img input link meta param source track wbr'.split()
SPECIAL_ELEMENTS = 'slot event scope react component'.split()
FORMATTED_EXPRESSION = re.compile(r'^([^{]|\{\{)*\{([^}]|\{\{|}})*}(?!})')

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

    def visitMacroBegin(self, ctx: PMLParser.MacroBeginContext):
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

            def parse_globals():
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

            text = parse_globals()

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


