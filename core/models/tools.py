from __future__ import annotations

import typing
import re

from pony.orm.core import Query, EntityMeta
from .runtime import find_entity_info, AttrInfo

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['AS', 'query_info']


def AS(expr, name):
    return expr


class ColSpecs(typing.NamedTuple):
    name: str
    title: str
    t: type


def query_info(q: Query) -> Optional[Dict[str, AttrInfo]]:
    if type(q) != Query:
        return None
    res = {}
    trans = q._translator

    if isinstance(trans.expr_type, EntityMeta):
        ent_info = find_entity_info(trans.expr_type)
        res = {name: ent_info[name] for name in trans.col_names if not ent_info[name].is_body and not ent_info[name].is_cid}
        return res

    for expr, col_name, col_type in zip(trans.expr_columns, trans.col_names, trans.expr_type):
        if expr[0] == 'COLUMN':
            ent_info = find_entity_info(trans.namespace[expr[1]].type)
            res[expr[2]] = ent_info[expr[2]]
        elif expr[0] == 'JSON_QUERY':
            name = q._vars[tuple(*[expr[2][0][1][0]])]
            ent_info = find_entity_info(trans.namespace[expr[1][1]].type)
            res[name] = ent_info[name]
        else:
            if col_name.startswith('AS('):
                name = re.search(query_info.re_as, col_name).group(1)
            else:
                name = expr[0]
            res[name] = AttrInfo(name=name, type=col_type, readonly=True)
    return res
query_info.re_as = re.compile(r'[\'"](.*?)[\'"]\s*\)$')
