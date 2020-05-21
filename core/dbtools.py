from __future__ import annotations

import typing
import re

from common import typename

if typing.TYPE_CHECKING:
    from typing import *
    from pony.orm.core import Query


def AS(expr, name):
    return expr


def query_columns(q: Query) -> Optional[List[Tuple(str, type)]]:
    if typename(q) != 'Query':
        return None
    res = []
    trans = q._translator
    for i, col in enumerate(trans.expr_columns):
        if col[0] == 'COLUMN':
            attrs = trans.namespace[col[1]].type._attrs_
            attr = next(attr for attr in attrs if attr.column == col[2])
            name = attr.title
        elif trans.col_names[i].startswith('AS('):
            name = re.search(query_columns.re_as, trans.col_names[i]).group(1)
        else:
            name = col[0]
        _type = trans.expr_type[i]
        res.append((name, _type))
    return res
query_columns.re_as = re.compile(r'\'(.*?)\'\)$')
