from typing import Mapping

from pony.orm import Required, dbapiprovider
from pony.orm.core import throw

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
