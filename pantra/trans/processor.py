from __future__ import annotations

import sys
import typing
import ast
from dataclasses import dataclass, field
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from babel.support import Translations, NullTranslations
from pantra.defaults import APPS_PATH, COMPONENTS_PATH
from .locale import Locale

if typing.TYPE_CHECKING:
    from typing import *
    from types import CodeType


class TranslationsExtra(Translations):
    def gettext(self, message):
        tmsg = self._catalog.get(message)
        if tmsg is None:
            tmsg = self._catalog.get((message, 0))
            if tmsg is None:
                return message
        return tmsg


@lru_cache(maxsize=None)
def get_locale(lang: str) -> Locale:
    return Locale.parse(lang)


# TODO: make compatible with file watcher
def get_translation(app_path: Path, lang: Union[str, Iterable]) -> Translations:
    lang_lst = (lang, 'en') if isinstance(lang, str) else lang
    transes = [
        TranslationsExtra.load(COMPONENTS_PATH / 'locale', lang_lst),
        Translations.load(APPS_PATH / 'system'/ 'locale', lang_lst),
        Translations.load(app_path / 'locale', lang_lst),
    ]
    trans = transes[0]
    for item in transes:
        if type(trans) is NullTranslations:
            trans = item
        else:
            trans.merge(item)
    return trans


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
        globals = sys._getframe(3).f_globals
        args = []
        for co in f_cache[f].args:
            args.append(eval(co, globals, locals))
        return f_cache[f].s, args

    node = ast.parse(f"f'''{f}'''", mode='eval')
    frame = sys._getframe(3)
    locals = frame.f_locals
    globals = frame.f_globals
    filename = frame.f_code.co_filename
    del frame

    def reveal(node):
        ex = ast.Expression(body=node)
        co = compile(ex, filename, 'eval')
        f_cache[f].args.append(co)
        args.append(eval(co, globals, locals))

    s = ''
    args = []
    for v in node.body.values:
        if type(v) == ast.Constant:
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


def zgettext(trans: Translations, message: str, *, plural: str = None, n: int = None, ctx: str = None, many: bool = False):
    if many:
        message = f'{message}s'
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

