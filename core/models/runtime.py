from __future__ import annotations

import typing
import json
import os
import types
from collections import defaultdict
from dataclasses import dataclass, field as dc_field
from datetime import datetime, time, timedelta, date
from decimal import Decimal
from functools import lru_cache
from uuid import UUID

from pony.orm import Database, Optional, Required, Discriminator, Set, LongStr, Json, StrArray, FloatArray, IntArray
from core.common import ADict
from .parser import parse_xml, expat
from .choicefield import Choice
from core.defaults import *

if typing.TYPE_CHECKING:
    from typing import *
    from pony.orm.core import EntityMeta

type_map = {
    'bool': bool,
    'int': int,
    'float': float,
    'str': str,
    'bytes': bytes,
    'Decimal': Decimal,
    'datetime': datetime,
    'date': date,
    'time': time,
    'timedelta': timedelta,
    'UUID': UUID,
    'LongStr': LongStr,
    'Json': Json,
}

type_factory = {
    'bool': lambda s: s != 'False',
    'int': int,
    'float': float,
    'str': str,
    'bytes': bytes,
    'Decimal': Decimal,
    'datetime': lambda s: datetime.strptime(s, '%d-%m-%Y %H:%M:%S'),
    'date': lambda s: datetime.strptime(s, '%m-%d-%Y').date(),
    'time': lambda s: datetime.strptime(s, '%H:%M:%S').time(),
    'timedelta': lambda s: timedelta(seconds=float(s)),
    'UUID': str,
    'LongStr': str,
    'Json': json.loads,
}

array_type_map = {
    'str': StrArray,
    'float': FloatArray,
    'int': IntArray,
}

@dataclass
class DatabaseFactory:
    cls: Database
    kwargs: Dict[str, Any]


@dataclass
class DatabaseInfo:
    factory: DatabaseFactory = dc_field(default=None)
    entities: Dict[str, 'EntityInfo'] = dc_field(default_factory=ADict)
    schema: str = dc_field(default_factory=str)


@dataclass
class EntityFactory:
    cls: type = dc_field(init=False)
    bases: list
    fields: Dict[str, Any]
    body: 'AttrInfo'
    has_cid: bool = dc_field(default=False)

    def __str__(self):
        return f'EntityFactory({self.cls.__name__})'


@dataclass
class EntityInfo:
    factory: EntityFactory = dc_field(default=None)
    attrs: Dict[str, AttrInfo] = dc_field(default_factory=ADict)
    schema: str = dc_field(default_factory=str)


@dataclass
class AttrInfo:
    name: str
    type: type = dc_field(default=None)
    title: str = dc_field(default='')
    width: int = dc_field(default=None)
    choices: Mapping = dc_field(default=None)
    blank: bool = dc_field(default=False)
    is_body: bool = dc_field(default=False)
    body: 'AttrInfo' = dc_field(init=False)
    readonly: bool = dc_field(default=False)

    def __str__(self):
        return f'AttrInfo({self.name})'

    def __repr__(self):
        return f'AttrInfo({self.name})'


dbinfo: Dict[str, Dict[str, DatabaseInfo]] = ADict()  # app / db / DatabaseInfo


def expose_models(app: str, app_info: Dict[str, DatabaseInfo] = None):
    file_name = os.path.join(APPS_PATH, app, 'data', 'models.xml')
    if not os.path.exists(file_name):
        return

    locals = {}

    # load python module
    in_python = False
    python = ''

    def start_python(name: str, attrs: dict):
        nonlocal in_python, python
        if name == 'python':
            in_python = True
            python = '\n' * p.CurrentLineNumber

    def end_python(name: str):
        nonlocal in_python, python
        if name == 'python':
            in_python = False
            code = compile(python, file_name, 'exec')
            exec(code, locals)

    def python_data(data):
        nonlocal python
        if in_python:
            python += data + '\n'

    p = expat.ParserCreate()
    parse_xml(file_name, start_python, end_python, python_data, parser=p)

    # expose entities
    fields = {}

    if not app_info:
        app_info = dbinfo[app]

    db_name: str
    entity_name: str
    entity_info: typing.Optional[EntityInfo]

    set_later: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)

    def collect_roots(base: str, db_info: Dict[str, EntityInfo], roots: typing.Set[str] = None):
        has_base = False
        for up in db_info[base].factory.bases:
            if isinstance(up, types.FunctionType):
                has_base = True
                collect_roots(up, db_info, roots)
        for attr_name, attr in db_info[base].attrs.items():
            if attr_name not in entity_info.attrs:
                entity_info.attrs[attr_name] = attr
        if not has_base:
            roots.add(base)

    def start_element(name: str, attrs: dict):
        nonlocal fields, entity_name, entity_info, db_name

        if name == 'entity':
            db_name = attrs.get('db', 'db')
            if db_name not in app_info:
                raise NameError(f'database to declared: {db_name}')
            db_info = app_info[db_name]
            entity_name = attrs['name']
            if entity_name not in db_info.entities:
                db_info.entities[entity_name] = EntityInfo()
            entity_info = db_info.entities[entity_name]
            entity_info.attrs['id'] = AttrInfo(name='id', type=int, title='#')

            body = None
            if 'base' in attrs:
                bases = []
                roots = set()
                for base in attrs['base'].split(','):
                    if base not in db_info.entities:
                        raise TypeError(f'can not find entity ({base}) in database {db_name}')
                    base_factory = db_info.entities[base.strip()].factory
                    if base_factory.body:
                        if body:
                            raise TypeError(f'can not use several bases with own bodies {entity_name}')
                        body = base_factory.body

                    collect_roots(base, db_info.entities, roots)
                    if len(roots) > 1:
                        raise TypeError(f'can not use several roots in entity inheritance {entity_name}')
                    root = roots.copy().pop()
                    if db_info.schema != db_info.entities[root].schema:
                        db_info.entities[root].schema = db_info.schema
                        db_info.entities[root].factory.fields['_table_'] = (db_info.schema, base.lower())
                    if not db_info.entities[root].factory.has_cid and 'classtype' not in entity_info.attrs:
                        entity_info.attrs['classtype'] = AttrInfo(name='classtype', type=str)
                    bases.append(lambda: base_factory.cls)
            else:
                db_info = app_info[db_name]
                bases = [db_info.factory.cls.Entity]
            if 'mixin' in attrs:
                bases.append(locals[attrs['mixin']])
            fields = {}
            if db_info.schema and 'base' not in attrs:
                fields['_table_'] = (db_info.schema, entity_name.lower())
            if 'cid' in attrs:
                fields['_discriminator_'] = int(attrs['cid'])
            if 'display' in attrs:
                display = attrs['display']
                fields['__str__'] = lambda self: eval(f'f"{display}"')
            for event in ('before_insert', 'before_update', 'before_delete', 'after_insert', 'after_update', 'after_delete'):
                if event in attrs:
                    fields[event] = locals[attrs[event]]

            entity_info.factory = EntityFactory(bases, fields, body)

        elif name in ('attr', 'array', 'prop'):
            attr_name = attrs['name']
            attr_info = AttrInfo(name=attr_name)
            entity_info.attrs[attr_name] = attr_info
            if name == 'prop':
                if not entity_info.factory.body:
                    raise TypeError(f'can not define prop {entity_name}.{attr_name} without "body" attr')
                attr_info.body = entity_info.factory.body
            if 'choices' in attrs:
                field = Choice
            elif attrs.get('cid', 'False') != 'False':
                field = Discriminator
                entity_info.factory.has_cid = True
            else:
                field = Optional if attrs.get('required', 'False') == 'False' else Required
            t = None
            type_name = ''
            kwargs = {}
            for a, v in attrs.items():
                if a == 'type':
                    type_name = v
                    if name != 'array':
                        if v in type_map:
                            t = type_map[v]
                            attr_info.type = t
                        else:
                            t = v
                            reverse_name = attrs.get('reverse', f'{entity_name.lower()}s')
                            set_later[v].append((db_name, reverse_name, entity_name))
                            attr_info.type = t
                    else:
                        field = array_type_map[v]
                        attr_info.type = list
                elif a == 'default':
                    kwargs[a] = type_factory[type_name](v)
                elif a == 'eval':
                    kwargs['default'] = eval(v, {'datetime': datetime}, locals)
                elif a == 'title':
                    attr_info.title = v
                elif a == 'width':
                    attr_info.width = float(v)
                elif a == 'choices':
                    attr_info.choices = locals[v]
                elif a == 'blank':
                    attr_info.blank = v == 'True'
                elif a == 'body':
                    entity_info.factory.body = attr_info
                elif a == 'precision':
                    kwargs[a] = int(v)
                elif a in ('sql_default', 'reverse'):
                    kwargs[a] = v
                elif a in ('unique', 'index'):
                    kwargs[a] = v != 'False'
            if name == 'array':
                fields[attr_name] = field(**kwargs)
            elif name == 'attr':
                fields[attr_name] = field(t, **kwargs)
            elif name == 'prop':
                body = attr_info.body.name
                prop = property(lambda self: getattr(self, body)[attr_name],
                                lambda self, value: getattr(self, body).__setitem__(attr_name, value))
                fields[attr_name] = prop

        elif name == 'set':
            attr_name = attrs['name']
            fields[attr_name] = Set(attrs['type'])

    parse_xml(file_name, start_element)

    # recover all missed Set fields
    for fk_name, lst in set_later.items():
        for db_name, reverse_name, entity_name in lst:
            if fk_name not in app_info[db_name].entities:
                raise TypeError(f'foreign model {fk_name} not found')
            fields = app_info[db_name].entities[fk_name].factory.fields
            if reverse_name not in fields:
                fields[reverse_name] = Set(entity_name)


def expose_datebases(app: str, with_binding: bool = True, with_mapping: bool = True, app_info: Dict[str, DatabaseInfo] = None) -> Optional[Database]:
    if not with_binding:
        with_mapping = False

    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        return None

    if app_info is None:
        if app not in dbinfo:
            dbinfo[app] = {}
        app_info = dbinfo[app]
        for_reuse = False
    else:
        for_reuse = True

    all_db = []

    def start_element(name: str, attrs: dict):
        nonlocal all_db, app_info
        if name != 'databases':
            kwargs = dict(attrs)
            db_name = kwargs.pop('name')
            schema = kwargs.pop('schema', '')
            if name == 'reuse':
                parent_app = kwargs.pop('app')
                expose_datebases(parent_app, app_info=app_info)
                app_info[db_name].schema = schema  # override schema
                all_db.append(app_info[db_name].factory.cls)
            else:
                kwargs['provider'] = name
                if with_binding:
                    db = Database(**kwargs)
                else:
                    db = Database()
                app_info[db_name] = DatabaseInfo(DatabaseFactory(cls=db, kwargs=kwargs), schema=schema)
                all_db.append(db)

    parse_xml(file_name, start_element)

    if not for_reuse:
        expose_models(app)

        # initialize entities
        for db in app_info.values():
            for ent_name, ent in db.entities.items():
                bases = []
                for base in ent.factory.bases:
                    if isinstance(base, types.FunctionType):
                        bases.append(base())
                    else:
                        bases.append(base)
                ent.factory.bases = bases
                ent.factory.cls = type(ent_name, tuple(bases), ent.factory.fields)

        # fill prop types
        for db in app_info.values():
            for ent in db.entities.values():
                for attr_info in ent.attrs.values():
                    if isinstance(attr_info.type, str):
                        attr_info.type = db.entities[attr_info.type].factory.cls

    else:
        expose_models(app, app_info)
        return None

    if with_mapping:
        for db in all_db:
            db.generate_mapping(create_tables=False, check_tables=False)

    if 'db' not in app_info:
        return None
    return app_info['db'].factory.cls


@lru_cache(maxsize=None)
def find_entity_info(entity: EntityMeta) -> Optional[Dict[str, AttrInfo]]:
    if not dbinfo:
        raise NameError('databases not exposed')

    for app in dbinfo.values():
        for db in app.values():
            for ent in db.entities.values():
                if ent.factory.cls == entity:
                    return ent.attrs

    raise NameError(f'entity is unknown ({entity.__class__.__name__})')
