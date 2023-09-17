from __future__ import annotations

import importlib
import os.path
import typing
import ast
import re
from xml.parsers import expat

from antlr4.error.ErrorListener import ErrorListener
from ..components.grammar.PMLLexer import PMLLexer
from ..components.grammar.PMLParser import PMLParser, InputStream, CommonTokenStream, IllegalStateException
from ..components.grammar.PMLParserVisitor import PMLParserVisitor
from ..defaults import BASE_PATH

if typing.TYPE_CHECKING:
    from typing import *


def drain_fstring(f):
    node = ast.parse(f"f'{f}'", mode='eval')

    s = ''
    for v in node.body.values:
        if type(v) == ast.Str:
            s += v.s
        elif type(v) == ast.FormattedValue:
            s += '{'
            if v.format_spec:
                s += ':'
                for vv in v.format_spec.values:
                    if type(vv) == ast.Str:
                        s += vv.s
                    elif type(vv) == ast.FormattedValue:
                        s += '{}'
            s += '}'
    return s


def extract_python(fileobj: Union[BinaryIO, str], keywords: List[str], comment_tags: List[str], options: List[str]) -> Iterator[Tuple[int, str, List[str], List[str]]]:
    """Extract messages from Python files. (borrowed from Babel)

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    if type(fileobj) == str:
        s = fileobj
    else:
        print(f'PY  > {fileobj.name}')
        s = fileobj.read()
        if type(s) is bytes:
            s = str(s, 'utf8')

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
            if len(node.args) != 1:
                warn('args count should be exactly one')
                continue
            ex = ast.Expression(body=node.args[0])
            msg = eval_ex(ex)
            if msg is None:
                continue
            msg = drain_fstring(msg)
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
                    messages.append(drain_fstring(kwargs['plural']))
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

    def visitRawTag(self, ctx:PMLParser.RawTagContext):
        tag_name = ctx.getText().strip()[1:]
        if tag_name == 'python':
            self.in_python = True

    def visitRawText(self, ctx:PMLParser.RawTextContext):
        if self.in_python:
            text = ctx.getText()
            if text.strip().strip('\uFEFF'):
                line_no = ctx.start.line
                text = '#\n' * (line_no - 1) + text
                for row in extract_python(text, *self.args):
                    self.res.append(row)

    def visitRawCloseTag(self, ctx:PMLParser.RawCloseTagContext):
        self.in_python = False

    def visitAttrValue(self, ctx:PMLParser.AttrValueContext):
        value = ctx.getText().strip('" \'')
        if value.startswith('#'):
            self.res.append((ctx.start.line, '_', value[1:], []))

    def visitText(self, ctx:PMLParser.TextContext):
        text = ctx.getText()
        if text.startswith('#'):
            self.res.append((ctx.start.line, '_', text[1:], []))


class ErrorVisitor(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"ERROR: line {line}:{column} {msg}")


def extract_html(fileobj, keywords, comment_tags, options):
    """
    Extract messages from HTML components
    """
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


def extract_xml(fileobj, keywords, comment_tags, options):
    print(f'XML > {fileobj.name}')
    p = expat.ParserCreate()
    entity_name: str = ''

    def start_element(name: str, attrs: dict):
        nonlocal entity_name
        if name == 'entity':
            entity_name = attrs['name']
            res.append((p.ErrorLineNumber, 'ngettext', (entity_name, f'{entity_name}s'), ['entity']))
            res.append((p.ErrorLineNumber, '_', f'{entity_name}s', ['entity plural']))
            if 'title' in attrs:
                title = attrs['title']
                res.append((p.ErrorLineNumber, 'ngettext', (title, f'{title}s'), [f'title of {entity_name}']))
                res.append((p.ErrorLineNumber, '_', f'{title}s', [f'title of {entity_name} plural']))

        if name in ('attr', 'prop'):
            if 'title' in attrs:
                title = attrs['title']
                res.append((p.ErrorLineNumber, '_', title, [f'title of {attrs["name"]} {name} of {entity_name}']))
            else:
                res.append((p.ErrorLineNumber, '_', attrs['name'], [f'{name} of {entity_name}']))

    p.StartElementHandler = start_element
    res = []
    p.ParseFile(fileobj)
    yield from res

def extract_data(fileobj, keywords, comment_tags, options):

    from quazy import DBFactory, DBTable

    if type(fileobj) == str:
        raise NotImplementedError
    else:
        print(f'DATA > {fileobj.name}')
        s = fileobj.read()
        if type(s) is bytes:
            s = str(s, 'utf8')

    root = ast.parse(s)
    lines = s.splitlines()

    path = fileobj.name
    path = os.path.relpath(path, BASE_PATH)
    if path.endswith('__init__.py'):
        path = path[:-len('/__init__.py')]
    path = path.replace(os.sep, '.')
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
