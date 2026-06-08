import re

from pygments.token import Other, Comment, Text, Punctuation, Name, Operator, String, Keyword, Number
from pygments.lexer import bygroups, using, inherit, default
from pygments.lexers.css import ScssLexer  # noqa
from pygments.lexers.python import PythonLexer  # noqa
from pygments.lexers.html import HtmlLexer  # noqa

def monkey_patching():
    ScssLexer.tokens['root'][-1:] = [
        (r'(?=[^;{}][;}])', Name.Attribute, 'attr'),
        (r'(?=[^;{}:]+:[^a-z])', Name.Attribute, 'attr'),
        ScssLexer.tokens['root'][-1],
    ]

monkey_patching()

class PantraLexer(HtmlLexer):
    name = 'Pantra'
    aliases = ['pantra']
    mimetypes = ['text/x-pantra']
    uri = 'https://github.com/zergos/pantra'
    version_added = '0.1'
    flags = re.M | re.S | re.DOTALL

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'(\{\{)([#/]?)', bygroups(Comment.Preproc, Text), 'macro'),
            (r'(<)(\s*)(python)(\s*)',
             bygroups(Punctuation, Text, Name.Tag, Text),
             ('python-content', 'tag')),
            (r'(<)(\s*)(style)(\s*)',
             bygroups(Punctuation, Text, Name.Tag, Text),
             ('cstyle-content', 'tag')),
            (r'(<)(\s*)([A-Z][\w:.-]+)',
             bygroups(Punctuation, Text, Name.Class), 'tag'),
            (r'(<)(\s*)(/)(\s*)([A-Z][\w:.-]+)(\s*)(>)',
             bygroups(Punctuation, Text, Punctuation, Text, Name.Component, Text,
                      Punctuation)),
            inherit,
        ],
        'macro': [
            (r'\s+', Text),
            (r'\}\}', Comment.Preproc, '#pop'),
            (r'(is)(\s+)(not)?(\s+)?([a-zA-Z_]\w*)',
             bygroups(Keyword, Text, Keyword, Text, Name.Function)),
            (r'(_|true|false|none|True|False|None)\b', Keyword.Pseudo),
            (r'(for|in|as|reversed|recursive|not|and|or|is|if|elif|else|import|'
             r'with(?:(?:out)?\s*context)?|scoped|ignore\s+missing)\b',
             Keyword),
            (r'#', Keyword),
            (r'forloop\b', Name.Builtin),
            (r'[a-zA-Z_][\w-]*', Name.Variable),
            (r'\.\w+', Name.Variable),
            (r':?"(\\\\|\\[^\\]|[^"\\])*"', String.Double),
            (r":?'(\\\\|\\[^\\]|[^'\\])*'", String.Single),
            (r'([{}()\[\]+\-*/%,:~]|[><=]=?|!=)', Operator),
            (r"[0-9](\.[0-9]*)?(eE[+-][0-9])?[flFLdD]?|"
             r"0[xX][0-9a-fA-F]+[Ll]?", Number),
        ],
        'tag': [
            (r'\s+', Text),
            (r'([\w:-]+\s*)(=)(\s*)', bygroups(Name.Attribute, Operator, Text),
             'attr'),
            (r'[\w:-]+', Name.Attribute),
            (r'(/?)(\s*)(>)', bygroups(Punctuation, Text, Punctuation), '#pop'),
        ],
        'python-content': [
            (r'(<)(\s*)(/)(\s*)(python)(\s*)(>)',
             bygroups(Punctuation, Text, Punctuation, Text, Name.Tag, Text,
                      Punctuation), '#pop'),
            (r'.+?(?=<\s*/\s*python\s*>)', using(PythonLexer)),
        ],
        'cstyle-content': [
            (r'(<)(\s*)(/)(\s*)(style)(\s*)(>)',
             bygroups(Punctuation, Text, Punctuation, Text, Name.Tag, Text,
                      Punctuation),'#pop'),
            (r'.+?(?=<\s*/\s*style\s*>)', using(ScssLexer)),
        ],
        'attr': [
            ('".*?"', String, '#pop'),
            ("'.*?'", String, '#pop'),
            (r'[^\s>]+', String, '#pop'),
        ]
    }
