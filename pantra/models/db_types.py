import inspect
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from uuid import UUID
from enum import IntEnum

__all__ = ['datetime', 'timedelta', 'date', 'time', 'Decimal', 'UUID', 'KNOWN_TYPES',
           'db_type_name', 'db_type_by_name', 'IntEnum']

KNOWN_TYPES = (
    int, str, float, bool, bytes,
    datetime, timedelta, date, time,
    Decimal,
    UUID,
    dict
)

TYPE_MAP = {
    'int': int,
    'str': str,
    'float': float,
    'bool': bool,
    'bytes': bytes,
    'datetime': datetime,
    'timedelta': timedelta,
    'date': date,
    'time': time,
    'Decimal': Decimal,
    'UUID': UUID,
    'dict': dict,
    'IntEnum': int,
}

def db_type_name(t: type) -> str:
    if t in KNOWN_TYPES:
        return t.__name__
    elif inspect.isclass(t) and issubclass(t, IntEnum):
        return 'IntEnum '+t.__name__
    else:
        raise TypeError(f"Unsupported field type {t}")

def db_type_by_name(name: str) -> type | str:
    if name in TYPE_MAP:
        return TYPE_MAP[name]
    elif name.startswith('IntEnum'):
        return name.split()[1]
    return name
