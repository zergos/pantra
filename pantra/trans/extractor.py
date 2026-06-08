from __future__ import annotations

from pathlib import Path
import importlib
import typing
import ast
import re
import html
import string

from antlr4.error.ErrorListener import ErrorListener

from .processor import demux_fstring
from ..settings import config
from ..components.loader import FORMATTED_EXPRESSION, FORMATTED_EXPRESSION2, UTF_BOM

from ..components.grammar.PMLLexer import PMLLexer
from ..components.grammar.PMLParser import PMLParser, InputStream, CommonTokenStream, IllegalStateException
from ..components.grammar.PMLParserVisitor import PMLParserVisitor

def extract_python(fileobj: str | typing.BinaryIO,
                   keywords: list[str],
                   comment_tags: list[str],
                   options: list[str]) -> typing.Iterator[tuple[int, str, list[str], list[str]]]:
    """Extract messages from Python files. (borrowed from Babel)

    Arguments:
        fileobj: the file-like object the messages should be extracted from
        keywords: a list of keywords (i.e. function names) that should
            be recognized as translation functions
        comment_tags: a list of translator tags to search for and
            include in the results
        options: a dictionary of additional options (optional)
    """
    s: str
    if type(fileobj) == str:
        s = fileobj
    else:
        print(f'PY  > {fileobj.name}')
        sb = fileobj.read()
        if type(sb) is bytes:
            s = str(sb, 'utf8')
        else:
            s = str(sb)

    root = ast.parse(s)
    lines = s.splitlines()

    def warn(mes):
        # seg = ast.get_source_segment()
        print(f'    INFO:{node.lineno}:{node.col_offset + 1} {mes}:')
        print(lines[node.lineno-1])
        print(' '*(node.col_offset+2) + '^')

    def eval_ex(ex: ast.Expression):
        co = compile(ex, '<string>', 'eval')
        try:
            return eval(co, {}, {})
        except:
            warn('skip runtime expression')

    for node in ast.walk(root):
        if type(node) == ast.Call and type(node.func) == ast.Name and node.func.id == '_':
            if len(node.args) < 1:
                warn('args count should be more then one')
                continue
            ex = ast.Expression(body=node.args[0])
            msg = eval_ex(ex)
            if msg is None:
                continue
            messages = []
            if node.keywords:
                ex = ast.Expression(body=node)
                node.func.id = 'dict'
                node.args.clear()
                kwargs = eval_ex(ex)
                if kwargs is None:
                    continue
                if 'ctx' in kwargs:
                    messages.append(kwargs['ctx'])
                messages.append(msg)
                if ('plural' in kwargs) != ('n' in kwargs):
                    warn("'plural' and 'n' should be set together")
                    continue
                if 'plural' in kwargs:
                    messages.append(kwargs['plural'])
                    messages.append(kwargs['n'])
                if 'plural' in kwargs and 'ctx' in kwargs:
                    func = 'npgettext'
                elif 'plural' in kwargs:
                    func = 'ngettext'
                else:
                    func = 'pgettext'
            else:
                messages.append(msg)
                func = '_'
            comments = []
            if node.lineno > 1:
                prev_line = lines[node.lineno - 2]
                if prev_line.strip().startswith('#'):
                    comment = prev_line.strip().strip('#').strip()
                    for tag in comment_tags:
                        if comment.startswith(f'{tag}:'):
                            comments.append(comment[len(tag) + 1:].strip())
            yield node.lineno, func, messages, comments


class MyVisitor(PMLParserVisitor):
    def __init__(self, args):
        self.in_python = False
        self.args = args
        self.res = []
        self._stripped_text = ""
        self._unstripped_text = ""

    def visitScriptTag(self, ctx:PMLParser.ScriptTagContext):
        tag_name = ctx.getText().strip()[1:]
        if tag_name == 'python':
            self.in_python = True

    def visitScriptText(self, ctx:PMLParser.ScriptTextContext):
        if self.in_python:
            text = ctx.getText()
            if text.strip().strip('\uFEFF'):
                line_no = ctx.start.line
                text = '#\n' * (line_no - 1) + text
                for row in extract_python(text, *self.args):
                    self.res.append(row)

    def visitScriptEnd(self, ctx:PMLParser.ScriptEndContext):
        self.in_python = False

    def _text_to_render(self, text: str, double_brackets: bool) -> str | None:
        if text in ('{}', '#', '::', '!', '@'):
            return text

        def template_i18n() -> str:
            text_demuxed, _ = demux_fstring(text)
            return text_demuxed

        translated = False
        while True:
            if text[0] == '!':
                text = text[1:]
                continue
            if text[0] == '#':
                text = text[1:]
                translated = True
                continue
            if text.startswith('::'):
                text = text[2:]
                continue
            break

        if not translated:
            return None

        if not double_brackets and FORMATTED_EXPRESSION.search(text):
            # check the whole string is an expression
            if text.startswith('{') and text.endswith('}') and text.count('}') == 1:
                return None
            # check for string template
            else:
                text = text.replace('`{', '{').replace('}`', '}')
                return template_i18n()

        elif double_brackets and FORMATTED_EXPRESSION2.search(text):
            # check the whole string is an expression
            if text.startswith('{{') and text.endswith('}}') and text.count('}}') == 1:
                return None
            # check for string template
            else:
                text = (text.replace('`{', '\u0007').replace('{{', '\u0007')
                        .replace('}`', '\u0008').replace('}}', '\u0008')
                        .replace('{', '{{').replace('}', '}}')
                        .replace('\u0007', '{').replace('\u0008', '}')
                        )
                return template_i18n()

        return text

    def visitAttrValue(self, ctx:PMLParser.AttrValueContext):
        text = ctx.getText().strip('"\'`')
        if ctx.stop.type in (ctx.parser.STRING, ctx.parser.EXPRESSION):
            rendered = self._text_to_render(text, False)
            if rendered:
                self.res.append((ctx.start.line, '_', rendered, []))

    def visitContent(self, ctx: PMLParser.ContentContext):
        self._stripped_text = ""
        self._unstripped_text = ""
        self.visitChildren(ctx)

        if self._unstripped_text.endswith('#') and not re.match(r'^#+$', self._stripped_text):
            content = self._unstripped_text[:-1]
        else:
            content = self._stripped_text
        if content:
            rendered = self._text_to_render(content, True)
            if rendered:
                self.res.append((ctx.start.line, '_', rendered, []))

    def visitText(self, ctx:PMLParser.TextContext):
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

class ErrorVisitor(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"ERROR: line {line}:{column} {msg}")


def extract_html(fileobj, keywords, comment_tags, options):
    """Extract messages from HTML components"""
    print(f'HTML> {fileobj.name}')
    in_stream = InputStream(fileobj.read().decode('utf-8'))
    lexer = PMLLexer(in_stream)
    stream = CommonTokenStream(lexer)
    parser = PMLParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorVisitor())
    tree = parser.process()

    visitor = MyVisitor((keywords, comment_tags, options))
    try:
        visitor.visit(tree)
    except IllegalStateException as e:
        print(f'ERROR: {str(e)}')
        return
    yield from visitor.res


def extract_data(fileobj, keywords, comment_tags, options):
    """Extract messages from `quazydb` derived classes"""
    try:
        from quazy import DBFactory, DBTable
    except ImportError as e:
        raise RuntimeError("quazydb is not installed") from e

    if type(fileobj) == str:
        raise NotImplementedError
    else:
        print(f'DATA > {fileobj.name}')
        s = fileobj.read()
        if type(s) is bytes:
            s = str(s, 'utf8')

    root = ast.parse(s)
    lines = s.splitlines()

    path = Path(fileobj.name)
    if path.name == '__init__.py':
        path = path.parent
    path = '.'.join(path.relative_to(config.BASE_PATH).parts)
    module = importlib.import_module(path)
    db: DBFactory = module.db
    all_tables = db.all_tables()

    def warn(node, mes):
        # seg = ast.get_source_segment()
        print(f'    INFO:{node.lineno}:{node.col_offset + 1} {mes}:')
        print(lines[node.lineno-1])
        print(' '*(node.col_offset+0) + '^')

    def plural(word):
        # https://www.geeksforgeeks.org/python-program-to-convert-singular-to-plural/
        if re.search('[sxz]$', word) or re.search('[^aeioudgkprt]h$', word):
            return re.sub('$', 'es', word)
        elif re.search('[aeiou]y$', word):
            return re.sub('y$', 'ies', word)
        else:
            return word + 's'

    for node in ast.walk(root):
        if type(node) == ast.ClassDef:
            yield node.lineno, 'ngettext', (node.name, plural(node.name)), ['entity']
            yield node.lineno, '_', plural(node.name), ['entity plural']
            table = next((table for table in all_tables if table.__name__ == node.name), None)
            
            if not table: continue
            for subnode in ast.iter_child_nodes(node):
                if type(subnode) == ast.AnnAssign \
                        and type(subnode.target) == ast.Name \
                        and type(subnode.target.ctx) == ast.Store:
                    field_name = subnode.target.id
                    if (field := table.DB.fields.get(field_name, None)) is not None:
                        yield subnode.lineno, '_', field_name, [f'field `{field_name}` of `{table.__qualname__}`']
                        if field.ux.title and field.ux.title != field_name:
                            yield subnode.lineno, '_', field.ux.title, [f'field title `{field_name}` of `{table.__qualname__}`']
                elif type(subnode) == ast.Assign \
                        and type(subnode.targets[0]) == ast.Name \
                        and subnode.targets[0].id == '_title_':
                    title = subnode.value.s
                    yield subnode.lineno, 'ngettext', (title, plural(title)), [f'title of `{table.__qualname__}`']
                    yield subnode.lineno, '_', plural(title), [f'title of `{table.__qualname__}` plural']
                elif type(subnode) == ast.ClassDef \
                    and subnode.bases[0].id in ('StrEnum', 'IntEnum'):
                    #print(subnode.lineno, '!')
                    for subsubnode in ast.iter_child_nodes(subnode):
                        if type(subsubnode) == ast.Assign \
                            and type(subsubnode.targets[0]) == ast.Name:
                            #print(subsubnode.lineno)
                            yield subsubnode.lineno, '_', subsubnode.targets[0].id, [f'enum value for `{subnode.name}`']
