from __future__ import annotations

import typing
import re

from pony.orm.core import Query, Entity

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['AS', 'query_columns']


def AS(expr, name):
    return expr


def query_columns(q: Query) -> Optional[List[Tuple(str, type)]]:
    if type(q) != Query:
        return None
    res = []
    trans = q._translator

    if isinstance(trans.expr_type, Entity):
        res = [(attr.title, attr.py_type) for name in trans.col_names for attr in [getattr(trans.expr_type, name)]]
        return res

    for expr, col_name, col_type in zip(trans.expr_columns, trans.col_names, trans.expr_type):
        if expr[0] == 'COLUMN':
            attrs = trans.namespace[expr[1]].type._attrs_
            name = next(attr.title for attr in attrs if attr.column == expr[2])
        elif col_name.startswith('AS('):
            name = re.search(query_columns.re_as, col_name).group(1)
        else:
            name = expr[0]
        res.append((name, col_type))
    return res
query_columns.re_as = re.compile(r'\'(.*?)\'\)$')
