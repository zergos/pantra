from __future__ import annotations

import typing
import enum

from quazy import DBTable, UX
from quazy.db_types import *
from pantra.components.context import Context
from pantra.common import ADict, WebUnits

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.components.context import AnyNode


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
        in_body=ux.field.prop,
    ) | kwargs
    if value is not None:
        locals['value'] = value
    if ux.field.type == int:
        locals['step'] = 1
    if ux.field.name == 'name':
        locals['focus'] = True
    if isinstance(ux.field.type, DBTable):
        template = 'DBField'
        locals['table'] = ux.field.type
    elif isinstance(ux.field.type, str) and ux.multiline:
        template = 'TextAreaField'
    else:
        template = TEMPLATE_MAP[ux.field.type]
        if not template:
            return None
    c = Context(template, parent, locals=locals)
    c.render.build()
    return c

