from __future__ import annotations

import typing
import re

from pony.orm.core import Query, Entity, EntityMeta, Required, throw
from pony.orm import dbapiprovider

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['AS', 'query_columns', 'Choice']


def AS(expr, name):
    return expr


class ColSpecs(typing.NamedTuple):
    name: str
    title: str
    t: type


def query_columns(q: Query) -> Optional[List[ColSpecs]]:
    if type(q) != Query:
        return None
    res = []
    trans = q._translator

    if isinstance(trans.expr_type, EntityMeta):
        res = [ColSpecs(name, attr.title, attr.py_type) for name in trans.col_names for attr in [getattr(trans.expr_type, name)]]
        return res

    for expr, col_name, col_type in zip(trans.expr_columns, trans.col_names, trans.expr_type):
        if expr[0] == 'COLUMN':
            attrs = trans.namespace[expr[1]].type._attrs_
            name, title = next((attr.name, attr.title) for attr in attrs if attr.column == expr[2])
        elif col_name.startswith('AS('):
            name = title = re.search(query_columns.re_as, col_name).group(1)
        else:
            name = title = expr[0]
        res.append(ColSpecs(name, title, col_type))
    return res
query_columns.re_as = re.compile(r'[\'"](.*?)[\'"]\s*\)$')


# next code based on example from https://gist.github.com/erickmendonca/c260cc945201e8ab31ebabb47d33c2a0
# Choice field for PonyORM similar to Django https://docs.djangoproject.com/en/2.0/ref/models/fields/#choices

# Use it like this:
# class SomeModel(db.Entity):
#     some_field = Choice(str, choices={
#         'key': 'Value',
#         'som': 'Something',
#         'ano': 'Another thing',
#     })


class Choice(Required):
    __slots__ = ('__choices',)

    def __init__(self, *args, choices=None, **kwargs):
        if not choices or not isinstance(choices, Mapping):
            throw(
                ValueError,
                'Choices argument must be a Mapping (dict) of sql_value: display_value instance'
            )
        if any(not isinstance(value, str) for value in choices):
            throw(
                ValueError,
                'Choices only support strings for sql_value',
            )
        super().__init__(*args, **kwargs)
        self.__choices = dict(**choices)

    def validate(self, val, *args, **kwargs):
        val = super().validate(val, *args, **kwargs)
        if val not in self.__choices.values():
            throw(
                ValueError,
                'Choice {} is not valid. Valid choices are {}.'.format(
                    val, self.__choices.values(),
                )
            )
        return val

    def get_display_value(self, sql_value):
        return self.__choices[sql_value]

    def get_sql_value(self, display_value):
        try:
            value = next(
                value for key, value in self.__choices.items()
                if value == display_value
            )
            return value
        except StopIteration:
            return None


class ChoiceConverter(dbapiprovider.StrConverter):
    def validate(self, val, obj=None):
        if not isinstance(val, Choice):
            throw(ValueError, 'Must be a Choice. Got {}'.format(type(val)))
        return val

    def py2sql(self, val):
        return val.name

    def sql2py(self, value):
        # Any enum type can be used, so py_type ensures the correct one is used to create the enum instance
        return self.py_type[value]


# monkey patching
try:
    from pony.orm.dbproviders.postgres import PGProvider
except:
    PGProvider = None
try:
    from pony.orm.dbproviders.mysql import MySQLProvider
except:
    MySQLProvider = None
try:
    from pony.orm.dbproviders.oracle import OraProvider
except:
    OraProvider = None
from pony.orm.dbproviders.sqlite import SQLiteProvider

for provider in (PGProvider, MySQLProvider, OraProvider, SQLiteProvider):
    if provider:
        provider.converter_classes.append((Choice, ChoiceConverter))
