from __future__ import annotations

import typing
import enum

try:
    from quazy import DBTable
    from quazy.db_types import *
except ImportError:
    DBTable = None
    from pantra.models.db_types import *

from pantra.components.context import Context
from pantra.common import ADict, WebUnits

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.components.context import AnyNode
    from quazy import UX


class DBFieldType(enum.Enum):
    CATALOG = enum.auto()
    DOCUMENT = enum.auto()
    OTHER = enum.auto()


class ValuesDict(ADict):
    def __getattr__(self, item):
        if item[0] == '_':
            return super().__getattr__(item)
        return self[item]['value']

    def __setattr__(self, key, value):
        if key[0] == '_':
            super().__setattr__(key, value)
        else:
            self[key]['value'] = value


TEMPLATE_MAP = {
    str: 'TextField',
    int: 'NumberField',
    float: 'NumberField',
    Decimal: 'NumberField',
    bool: 'CheckField',
    date: 'DateField',
    time: 'TimeField',
    datetime: 'DateTimeField',
    timedelta: None,  # TODO
    bytes: None,
    #LongStr: 'TextAreaField',
    dict: 'TextAreaField',
    UUID: None,  # TODO
}


def make_widget(parent: AnyNode, ux: UX, value: Any = None, **kwargs) -> Optional[Context]:
    locals = ADict(
        caption=parent.session.gettext(ux.title),
        readonly=ux.readonly,
        required=not ux.blank,
        width='' if not ux.width else WebUnits(ux.width, 'em'),
    ) | kwargs
    if value is not None:
        locals['value'] = value
    if ux.type == int:
        locals['step'] = 1
    if ux.name == 'name':
        locals['focus'] = True
    if isinstance(ux.type, DBTable):
        template = 'DBField'
        locals['table'] = ux.type
    elif issubclass(ux.type, str) and ux.multiline:
        template = 'TextAreaField'
    elif issubclass(ux.type, enum.Enum):
        locals['enum_type'] = ux.type
        template = 'EnumField'
    else:
        template = TEMPLATE_MAP.get(ux.type, None)
        if not template:
            return None
    c = Context(template, parent, locals=locals)
    c.render.build()
    return c

