from __future__ import annotations

import hashlib
from pathlib import Path
import re
import typing
import html
import string

import cssutils
import sass
from antlr4 import FileStream, CommonTokenStream, IllegalStateException
from antlr4.error.ErrorListener import ErrorListener
from cssutils.css import CSSMediaRule, CSSStyleRule

from .grammar.PMLLexer import PMLLexer
from .grammar.PMLParser import PMLParser
from .grammar.PMLParserVisitor import PMLParserVisitor

from pantra.settings import config
from pantra.trans.processor import demux_fstring
from .template import HTMLTemplate, MacroCode, MacroType
from .static import get_static_url

__all__ = ['load', 'load_styles']

UTF_BOM = '\uFEFF'
VOID_ELEMENTS = 'area base br col embed hr img input link meta param source track wbr'.split()
SPECIAL_ELEMENTS = 'slot event scope react component'.split()
VARNAME_REFERENCE = re.compile(r'^@[a-zA-Z_][a-zA-Z0-9_]*$')
FORMATTED_EXPRESSION = re.compile(r'^([^{]|\{\{)*\{([^}]|\{\{|}})*}(?!})')
FORMATTED_EXPRESSION2 = re.compile(r'^([^{]|[{][^{]|`[^{])*(\{\{|`\{)(.*?)(}}|}`)')
MACRO_CHUNKS = re.compile(r"^(\w+(:\w+)?)\s+(.*)$", re.M | re.DOTALL)

class HTMLVisitor(PMLParserVisitor):

    def __init__(self, filename: Path):
        name = Path(filename).stem
        root = HTMLTemplate(f'${name}')
        root.filename = filename
        self.root: typing.Optional[HTMLTemplate] = root
        self.current: typing.Optional[HTMLTemplate] = root
        self.cur_attr: typing.Optional[str] = None
        self._script_index = 0

        self._stripped_text: str = ""
        self._unstripped_text: str = ""

    def visitScriptText(self, ctx: PMLParser.ScriptTextContext):
        text = ctx.getText()
        if text.strip(UTF_BOM):
            tag_name = self.current.tag_name
            if tag_name == '@python':
                line_no = ctx.start.line
                text = '#\n' * (line_no - 1) + text
            elif tag_name == '@script':
                text = self._text_to_code(text, True)
            self.current.content = text

    def visitScriptTag(self, ctx: PMLParser.ScriptTagContext):
        tag_name = '@' + ctx.getText().strip()[1:]
        self.current = HTMLTemplate(tag_name, parent=self.current)
        self.current.filename = self.root.filename
        # raw nodes goes first
        if tag_name == "@python":
            self.current.parent.children.insert(0, self.current.parent.children.pop())
        elif tag_name == "@script":
            self.current.script_index = self._script_index + 1
            self._script_index += 1

    def visitScriptEnd(self, ctx: PMLParser.ScriptEndContext):
        self.current = self.current.parent

    def visitTagOpen(self, ctx: PMLParser.TagOpenContext):
        tag_name = ctx.children[1].getText()
        if tag_name in SPECIAL_ELEMENTS:
            tag_name = '@' + tag_name
        self.current = HTMLTemplate(tag_name, parent=self.current)
        # if not self.root: self.root = self.current
        self.visitChildren(ctx)
        if ctx.children[-1].symbol.type == PMLLexer.TAG_SLASH_END or self.current.tag_name.lower() in VOID_ELEMENTS:
            self.current = self.current.parent

    def visitAttrName(self, ctx: PMLParser.AttrNameContext):
        self.cur_attr = ctx.getText()
        if self.cur_attr != 'class':
            self.current.set_attr(self.cur_attr, None)

    def _text_to_code(self, text: str, double_brackets: bool) -> str | MacroCode:
        if text in ('{}', '#', '::', '!', '@'):
            return text

        def template_i18n() -> MacroCode:
            nonlocal text
            if translated:
                text, args = demux_fstring(text)
                if len(args)>1:
                    args_text = '*((' + '), ('.join(args) + '))'
                elif len(args)==1:
                    args_text = args[0]
                else:
                    args_text = '*()'
                text = f'session.zgettext({text!r}, {args_text})'
            else:
                text = f'f"""{text}"""'
            return MacroCode(MacroType.TEMPLATE, reactive, evaluated,
                              compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)

        reactive, translated, evaluated = False, False, False
        while True:
            if text[0] == '!':
                reactive = True
                text = text[1:]
                continue
            if text[0] == '#':
                translated = True
                text = text[1:]
                continue
            if text.startswith('::'):
                evaluated = True
                text = text[2:]
                continue
            break

        if not double_brackets and (FORMATTED_EXPRESSION.search(text) or VARNAME_REFERENCE.match(text)):
            # override reactiveness for attributes
            if 'reactive' in self.current.attributes:
                reactive = True

            # check the whole string is an expression
            if text.startswith('{') and text.endswith('}') and text.count('}') == 1 or text.startswith('@'):
                if text.startswith('{'):
                    text = text[1:-1]
                else:
                    text = text[1:]
                return MacroCode(MacroType.VALUE, reactive, evaluated,
                              compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)
            # check for string template
            else:
                text = text.replace('`{', '{').replace('}`', '}')
                return template_i18n()

        elif double_brackets and FORMATTED_EXPRESSION2.search(text):
            # check the whole string is an expression
            if text.startswith('{{') and text.endswith('}}') and text.count('}}') == 1:
                text = text[2:-2]
                return MacroCode(MacroType.VALUE, reactive, evaluated,
                              compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)
            # check for string template
            else:
                text = (text.replace('`{', '\u0007').replace('{{', '\u0007')
                        .replace('}`', '\u0008').replace('}}', '\u0008')
                        .replace('{', '{{').replace('}', '}}')
                        .replace('\u0007', '{').replace('\u0008', '}')
                        )
                return template_i18n()

        elif translated:
            text = f'ctx.session.gettext("""{text}""")'
            return MacroCode(MacroType.STRING, False, True,
                              compile(text, f'<{self.current.path()}:{self.cur_attr}>', 'eval'), text)
        return text

    def visitAttrValue(self, ctx: PMLParser.AttrValueContext):
        text: str = ctx.getText().strip('"\'`')
        if ctx.stop.type == ctx.parser.NUMBER:
            try:
                value = int(text)
            except ValueError:
                value = float(text)

        elif ctx.stop.type == ctx.parser.BOOLEAN:
            value = text.lower() == 'true'

        else:
            value = self._text_to_code(text, False)

        self.current.set_attr(self.cur_attr, value)

    def visitContent(self, ctx: PMLParser.ContentContext):
        self._stripped_text = ""
        self._unstripped_text = ""
        self.visitChildren(ctx)

        if self._unstripped_text.endswith('#') and not re.match(r'^#+$', self._stripped_text):
            content = self._unstripped_text[:-1]
        else:
            content = self._stripped_text
        if content:
            HTMLTemplate("@text", self.current,
                         text=self._text_to_code(content, True))

    def visitText(self, ctx: PMLParser.TextContext):
        if self.current == self.root:
            return

        text = ctx.getText().lstrip(UTF_BOM)
        text = html.unescape(text)
        if (self._unstripped_text and
                (self._unstripped_text[-1] in string.whitespace
                 or text[0] in string.whitespace)):
            self._stripped_text += " "
        self._stripped_text += re.sub(r"\s+", " ", text.strip())
        self._unstripped_text += text

    def visitMacroInline(self, ctx: PMLParser.MacroInlineContext):
        if text:=ctx.getText().strip():
            if self._unstripped_text and self._unstripped_text[-1] in string.whitespace:
                self._stripped_text += ' '
            self._stripped_text += text
            self._unstripped_text += text

    def visitScriptName(self, ctx:PMLParser.ScriptNameContext):
        self.cur_attr = ctx.getText()
        self.current.set_attr(self.cur_attr, None)

    def visitScriptValue(self, ctx:PMLParser.ScriptValueContext):
        self.current.set_attr(self.cur_attr, ctx.getText().strip('"\''))

    def visitTagClose(self, ctx: PMLParser.TagCloseContext):
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

    def visitMacroOpen(self, ctx: PMLParser.MacroOpenContext):
        reactive = ctx.children[0].getText().startswith('!')
        command = ctx.children[1].getText()

        macro_chunks = MACRO_CHUNKS.search(command)
        if not macro_chunks:
            tag_name = command.strip()
            text = ''
        else:
            tag_name = macro_chunks.group(1).strip()
            text = macro_chunks.group(3).strip()

        # gen 'if' subtree
        if tag_name == 'if':
            parent = HTMLTemplate('#if', self.current)
            self.current = HTMLTemplate('#choice', parent=parent)
            self.current.set_attr('condition',
                                  MacroCode(MacroType.BOOLEAN, reactive, False,
                                            compile(text, f"<{self.current.path()}>", "eval"), text))
        elif tag_name == 'for':
            parent = HTMLTemplate('#for', self.current)
            sides = text.split('#')
            chunks = sides[0].split(' in ')
            var_name = chunks[0].strip()
            iterator = compile(chunks[1], f"<{parent.path()}:iterator>", "eval")
            index_func = compile(sides[1], f"<{parent.path()}:index_func>", "eval") if len(sides) > 1 else None

            self.current = HTMLTemplate('#loop', parent=parent)
            self.current.set_attr('var_name', var_name)
            self.current.set_attr('iter',
                                  MacroCode(MacroType.ITERATOR, reactive, False, iterator, chunks[1]))
            if len(sides)>1:
                self.current.set_attr('index_func',
                                      MacroCode(MacroType.INDEX, False, False, index_func, sides[1]))
        elif tag_name == 'elif':
            self.current = HTMLTemplate('#choice', parent=self.current.parent)
            self.current.set_attr('condition',
                                  MacroCode(MacroType.BOOLEAN, reactive, False, compile(text, f"<{self.current.path()}>", "eval"), text))
        elif tag_name == 'else':
            self.current = HTMLTemplate('#else', parent=self.current.parent)
        elif tag_name.startswith('set'):
            self.current = HTMLTemplate('#' + tag_name, parent=self.current)
            if '=' not in text:
                raise IllegalStateException("set command should contain an assignment expression")

            for line in text.splitlines():
                if not line.strip():
                    continue

                if ':=' in line:
                    var_name, code = line.split(':=', 1)
                else:

                    var_name, code = line.split('=', 1)
                expr = compile(code.strip(), f"<{self.current.path()}>", "eval")
                self.current.set_attr(var_name.strip(),
                                      MacroCode(MacroType.VALUE, reactive, False, expr, code.strip()))

    def visitMacroClose(self, ctx: PMLParser.MacroCloseContext):
        macro_tag = '#'+ctx.children[1].getText().strip()
        while self.current:
            if macro_tag == self.current.tag_name:
                break
            self.current = self.current.parent
        else:
            raise IllegalStateException(f"macro close tag don't match {macro_tag}")
        self.current = self.current.parent

    def visitErrorNode(self, node):
        raise IllegalStateException(f'wrong node {node.getText()}')


class ErrorCatcher(ErrorListener):
    def __init__(self, filename, error_callback):
        super().__init__()
        self.filename = filename
        self.error_callback = error_callback

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.error_callback(f"{self.filename}: line {line}:{column} {msg}")


def load(filename: Path, error_callback: typing.Callable[[str], None]) -> typing.Optional[HTMLTemplate]:
    in_stream = FileStream(str(filename), encoding='utf-8')
    lexer = PMLLexer(in_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(ErrorCatcher(filename, error_callback))
    stream = CommonTokenStream(lexer)
    parser = PMLParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorCatcher(filename, error_callback))
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
        HTMLTemplate("@python", visitor.root, text=code_filename.read_text(encoding='utf-8'))
        # raw nodes goes first
        visitor.root.children.insert(0, visitor.root.children.pop())

    res: HTMLTemplate = visitor.root
    res.hex_digest = hashlib.md5(Path(filename).read_bytes()).hexdigest()
    return res


class StyleVisitor(PMLParserVisitor):
    parser = cssutils.CSSParser(validate=False, raiseExceptions=True)

    def __init__(self, app:str, class_name: str, template_filename: Path):
        self.app = app
        self.class_name = class_name
        self.template_filename = template_filename
        self.styles: typing.List[str] = []
        self.in_style = False
        self.global_mode = False

    def visitScriptText(self, ctx: PMLParser.ScriptTextContext):
        if not self.in_style:
            return

        def static(file_name) -> str:
            return f'url("{get_static_url(self.app, self.template_filename.parent, self.class_name, None, file_name)}")'

        text = ctx.getText()
        text = '\n' * (ctx.start.line-1) + text
        text = sass.compile(string=text, output_style='compact', include_paths=[str(config.CSS_PATH.parent)], custom_functions=[
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

    def visitScriptName(self, ctx: PMLParser.ScriptNameContext):
        name = ctx.getText()
        if name == 'global':
            self.global_mode = True

    def visitScriptTag(self, ctx: PMLParser.ScriptTagContext):
        if ctx.getText().strip()[1:] == 'style':
            self.in_style = True
            self.global_mode = False

    def visitScriptEnd(self, ctx: PMLParser.ScriptEndContext):
        self.in_style = False

    def visitErrorNode(self, node):
        raise IllegalStateException(f'wrong node {node.getText()}')


def load_styles(app:str, name: str, template_filename: Path,
                error_callback: typing.Callable[[str], None] | None = None):
    in_stream = FileStream(str(template_filename), encoding='utf-8')
    lexer = PMLLexer(in_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(ErrorCatcher(str(template_filename), error_callback))
    stream = CommonTokenStream(lexer)
    parser = PMLParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorCatcher(str(template_filename), error_callback))
    tree = parser.process()

    visitor = StyleVisitor(app, name, template_filename)
    visitor.visit(tree)
    return '\n'.join(visitor.styles)


