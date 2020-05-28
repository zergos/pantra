from __future__ import annotations

import typing
import re

from pony.orm.core import Query, Entity

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['AS', 'query_columns']


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

    if isinstance(trans.expr_type, Entity):
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

