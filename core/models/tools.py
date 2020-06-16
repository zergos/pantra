from __future__ import annotations

import typing
import re

from pony.orm.core import Query, EntityMeta
from .runtime import find_entity_info

if typing.TYPE_CHECKING:
    from typing import *
    from .runtime import AttrInfo

__all__ = ['AS', 'query_info']


def AS(expr, name):
    return expr


class ColSpecs(typing.NamedTuple):
    name: str
    title: str
    t: type


def query_info(q: Query) -> Optional[List[AttrInfo]]:
    if type(q) != Query:
        return None
    res = []
    trans = q._translator

    if isinstance(trans.expr_type, EntityMeta):
        ent_info = find_entity_info(trans.expr_type)
        res = [ent_info[name] for name in trans.col_names]
        return res

    for expr, col_name, col_type in zip(trans.expr_columns, trans.col_names, trans.expr_type):
        if expr[0] == 'COLUMN':
            ent_info = find_entity_info(trans.namespace[expr[1]].type)
            res.append(ent_info[expr[2]])
        else:
            if col_name.startswith('AS('):
                name = re.search(query_info.re_as, col_name).group(1)
            else:
                name = expr[0]
            res.append(AttrInfo(name=name, type=col_type, readonly=True))
    return res
query_info.re_as = re.compile(r'[\'"](.*?)[\'"]\s*\)$')
