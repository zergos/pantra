from __future__ import annotations

import typing
import enum

from pantra.components.context import Context
from pantra.models.types import *
from pantra.common import ADict, WebUnits

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.models.runtime import AttrInfo
    from pantra.components.context import AnyNode


class EntityType(enum.Enum):
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
    LongStr: 'TextAreaField',
    Json: 'TextAreaField',
    UUID: None,  # TODO
}


def make_widget(parent: AnyNode, attr: AttrInfo, value: Any = None, **kwargs) -> Optional[Context]:
    locals = ADict(
        caption=parent.session.gettext(attr.title),
        readonly=attr.readonly,
        required=not attr.blank,
        width='' if not attr.width else WebUnits(attr.width, 'em'),
        in_body=hasattr(attr, 'body'),
    ) | kwargs
    if value is not None:
        locals['value'] = value
    if attr.type == int:
        locals['step'] = 1
    if attr.name == 'name':
        locals['focus'] = True
    if isinstance(attr.type, EntityMeta):
        template = 'EntityField'
        locals['entity'] = attr.type
    else:
        attr_type = attr.type
        if attr_type is LongStr and kwargs.get('flat'):
            attr_type = str
        template = TEMPLATE_MAP[attr_type]
        if not template:
            return None
    c = Context(template, parent, locals=locals)
    c.render.build()
    return c

