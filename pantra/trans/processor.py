from __future__ import annotations

import sys
import typing
import ast
from functools import lru_cache

from babel.support import Translations, NullTranslations
from pantra.settings import config
from .locale import Locale


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
def get_translation(app: str, lang: str | typing.Iterable) -> Translations:
    lang_lst = (lang, 'en') if isinstance(lang, str) else lang
    transes = [
        TranslationsExtra.load(config.COMPONENTS_PATH / 'locale', lang_lst),
        Translations.load(config.APPS_PATH / 'system' / 'locale', lang_lst),
        Translations.load(config.APPS_PATH / app / 'locale', lang_lst),
    ]

    trans = transes[0]
    for item in transes:
        if type(trans) is NullTranslations:
            trans = item
        else:
            trans.merge(item)
    return trans


def demux_fstring(f) -> tuple[str, list[str]]:
    node = ast.parse(f"f'''{f}'''", mode='eval')

    if sys.version_info < (3, 14):
        str_term = ast.Str
    else:
        str_term = ast.Constant

    s = ''
    args = []
    for v in node.body.values:
        if type(v) == ast.Constant:
            s += v.s
        elif type(v) == ast.FormattedValue:
            s += '{'
            if v.conversion > 0 and chr(v.conversion) == "r":
                args.append(f'repr({ast.unparse(v.value)})')
            else:
                args.append(ast.unparse(v.value))
            if v.format_spec:
                s += ':'
                for vv in v.format_spec.values:
                    if type(vv) == str_term:
                        s += vv.s
                    elif type(vv) == ast.FormattedValue:
                        s += '{}'
                        args.append(ast.unparse(vv.value))
            s += '}'
    return s, args


def zgettext(trans: Translations, message: str, *args, plural: str = None, n: int = None, ctx: str = None, many: bool = False):
    if many:
        message = f'{message}s'
    if plural is None and ctx is None:
        t = trans.gettext(message)
    elif plural is not None:
        if ctx is not None:
            t = trans.npgettext(ctx, message, plural, n)
        else:
            t = trans.ngettext(message, plural, n)
    else: # if ctx is not None:
        t = trans.pgettext(ctx, message)
    if args: t = t.format(*args)
    return t
