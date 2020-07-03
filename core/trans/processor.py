from __future__ import annotations

import os
import sys
import typing
import ast
from dataclasses import dataclass, field
from collections import defaultdict
from functools import lru_cache

from babel.support import Translations
from .locale import Locale

if typing.TYPE_CHECKING:
    from typing import *
    from types import CodeType


@lru_cache(maxsize=None)
def get_locale(lang: str) -> Locale:
    return Locale.parse(lang)


# TODO: make compatible with file watcher
def get_translation(app_path: str, lang: Union[str, Iterable]) -> Translations:
    lang_lst = (lang, 'en') if isinstance(lang, str) else lang
    return Translations.load(os.path.join(app_path, 'locale'), lang_lst)


@dataclass
class FRecord:
    s: str = field(default_factory=str)
    args: List[CodeType] = field(default_factory=list)


f_cache: Dict[str, FRecord] = defaultdict(FRecord)


def eval_fstring(f) -> Tuple[str, Optional[List[Any]]]:
    if f in f_cache:
        if not f_cache[f].args:
            return f, None
        locals = sys._getframe(3).f_locals
        args = []
        for co in f_cache[f].args:
            args.append(eval(co, locals))
        return f_cache[f].s, f_cache[f].args

    node = ast.parse(f"f'{f}'", mode='eval')
    frame = sys._getframe(3)
    locals = frame.f_locals
    filename = frame.f_code.co_filename
    del frame

    def reveal(node):
        ex = ast.Expression(body=node)
        co = compile(ex, filename, 'eval')
        f_cache[f].args.append(co)
        args.append(eval(co, locals))

    s = ''
    args = []
    for v in node.body.values:
        if type(v) == ast.Str:
            s += v.s
        elif type(v) == ast.FormattedValue:
            s += '{'
            reveal(v.value)
            if v.format_spec:
                s += ':'
                for vv in v.format_spec.values:
                    if type(vv) == ast.Str:
                        s += vv.s
                    elif type(vv) == ast.FormattedValue:
                        s += '{}'
                        reveal(vv.value)
            s += '}'
    f_cache[f].s = s
    return s, args


def zgettext(trans: Translations, message: str, *, plural: str = None, n: int = None, ctx: str = None):
    if plural is None and ctx is None:
        s, args = eval_fstring(message)
        t = trans.gettext(s)
    elif plural is not None:
        s, args = eval_fstring(message)
        s2, args2 = eval_fstring(plural)
        if ctx is not None:
            t = trans.npgettext(ctx, s, s2, n)
        else:
            t = trans.ngettext(s, s2, n)
    else:
        s, args = eval_fstring(message)
        t = trans.pgettext(ctx, s)
    if args: t = t.format(*args)
    return t


