from __future__ import annotations

import typing
import re
from functools import lru_cache

from pony.orm.core import Query, EntityMeta, EntityProxy, Entity
from .runtime import AttrInfo, dbinfo

if typing.TYPE_CHECKING:
    from typing import *
    from .types import AnyEntity
    from .runtime import EntityInfo

__all__ = ['AS', 'query_info', 'entity_name', 'get_entity', 'find_entity_info']


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
        attrs = find_entity_info(trans.expr_type).attrs
        res = {name: attrs[name] for name in trans.col_names if name != 'id' and not attrs[name].is_body and not attrs[name].is_cid}
        return res

    for expr, col_name, col_type in zip(trans.expr_columns, trans.col_names, trans.expr_type):
        if expr[0] == 'COLUMN':
            attrs = find_entity_info(trans.namespace[expr[1]].type).attrs
            res[expr[2]] = attrs[expr[2]]
        elif expr[0] == 'JSON_QUERY':
            name = q._vars[tuple(*[expr[2][0][1][0]])]
            attrs = find_entity_info(trans.namespace[expr[1][1]].type).attrs
            res[name] = attrs[name]
        else:
            if col_name.startswith('AS('):
                name = re.search(query_info.re_as, col_name).group(1)
            else:
                name = expr[0]
            res[name] = AttrInfo(name=name, type=col_type, title=name, readonly=True)
    return res
query_info.re_as = re.compile(r'[\'"]([^\'"]*?)[\'"]\s*\)+$')


def entity_name(ent):
    if isinstance(ent, EntityProxy):
        return ent._entity_.__name__
    elif isinstance(ent, Entity):
        return ent.__class__.__name__
    else:  # EntityMeta
        return ent.__name__


def get_entity(ent: AnyEntity) -> Optional[EntityMeta]:
    if isinstance(ent, EntityProxy):
        return ent._entity_
    elif isinstance(ent, Entity):
        return ent
    elif hasattr(ent, '_entity_'):
        return ent._entity_
    else:
        return None


@lru_cache(maxsize=None)
def _find_entity_info_cached(entity: EntityMeta) -> EntityInfo:
    if not dbinfo:
        raise NameError('databases not exposed')

    for app in dbinfo.values():
        for db in app.values():
            for ent in db.entities.values():
                if ent.factory.cls == entity:
                    return ent

    raise NameError(f'entity is unknown ({entity.__name__})')


def find_entity_info(entity: AnyEntity) -> Optional[EntityInfo]:
    if type(entity) == EntityMeta:
        return _find_entity_info_cached(entity)
    elif isinstance(entity, Entity):
        return _find_entity_info_cached(type(entity))
    else:  # EntityProxy
        return _find_entity_info_cached(entity._entity_)
