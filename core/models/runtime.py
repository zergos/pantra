from __future__ import annotations

import typing
import json
import os
import types
from collections import defaultdict
from dataclasses import dataclass, field as dc_field
from datetime import datetime, time, timedelta, date
from decimal import Decimal
from uuid import UUID

from pony.orm import Database, Optional, Required, Discriminator, Set, LongStr, Json, StrArray, FloatArray, IntArray
from core.common import ADict
from .parser import parse_xml, expat
from .choicefield import Choice
from core.defaults import *

if typing.TYPE_CHECKING:
    from typing import *

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
class DatabaseInfo:
    cls: Database
    kwargs: Dict[str, Any]


@dataclass
class EntityInfo:
    cls: type = dc_field(init=False)
    bases: list
    fields: Dict[str, Any]
    body: 'AttrInfo'


@dataclass
class AttrInfo:
    name: str
    type: type = dc_field(init=False)
    title: str
    width: int = dc_field(default=None)
    choices: Mapping = dc_field(default=None)
    blank: bool = dc_field(default=False)
    body: 'AttrInfo' = dc_field(init=False)


dbinfo: Dict[str, Dict[str, Union[Dict[str, Union[AttrInfo, EntityInfo]], DatabaseInfo]]] = ADict()  # app / entity+db / column / attr: value


def expose_models(db: Database, schema: Optional[str], app: str, app_info: Dict = None):
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
            python += data

    p = expat.ParserCreate()
    parse_xml(file_name, start_python, end_python, python_data, parser=p)

    # expose entities
    fields = {}

    if not app_info:
        if app not in dbinfo:
            dbinfo[app] = ADict()
        app_info = dbinfo[app]
    entity_name = ''
    entity_info = None

    set_later: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

    def collect_roots(base, roots: typing.Set[str] = None):
        has_base = False
        for up in app_info[base]['_init'].bases:
            if isinstance(up, types.FunctionType):
                has_base = True
                collect_roots(up, roots)
        if not has_base:
            roots.add(base)

    def start_element(name: str, attrs: dict):
        nonlocal fields, entity_name, entity_info

        if name == 'entity':
            actual_db_info = app_info['db']
            body = None
            if 'base' in attrs:
                bases = []
                roots = set()
                for b in attrs['base'].split(','):
                    init_info = app_info[b.strip()]['_init']
                    if init_info.body:
                        if body:
                            raise TypeError(f'can not use several bases with own bodies {attrs["name"]}')
                        body = init_info.body
                    if schema and 'db' not in attrs:
                        collect_roots(b, roots)
                        if len(roots) > 1:
                            raise TypeError(f'can not use several roots in entity inheritance {attrs["name"]}')
                        app_info[roots.copy().pop()]['_init'].fields['_table_'] = (schema, b.lower())
                    bases.append(lambda: init_info.cls)
            elif 'db' in attrs:
                actual_db_info = app_info[attrs['db']]
                bases = [actual_db_info.cls.Entity]
            else:
                bases = [db.Entity]
            if 'mixin' in attrs:
                bases.append(locals[attrs['mixin']])
            entity_name = attrs['name']
            fields = {}
            if schema and 'db' not in attrs and 'base' not in attrs:
                fields['_table_'] = (schema, entity_name.lower())
            if 'cid' in attrs:
                fields['_discriminator_'] = int(attrs['cid'])
            if 'display' in attrs:
                display = attrs['display']
                code = compile(display, '<string>', 'eval')
                fields['__str__'] = lambda self: eval(code)
            for event in ('before_insert', 'before_update', 'before_delete', 'after_insert', 'after_update', 'after_delete'):
                if event in attrs:
                    fields[event] = locals[attrs[event]]

            if entity_name not in app_info:
                app_info[entity_name] = ADict({'db': actual_db_info.cls})
            entity_info = app_info[entity_name]
            entity_info['_init'] = EntityInfo(bases, fields, body)

        elif name in ('attr', 'array', 'prop'):
            attr_name = attrs['name']
            attr_info = AttrInfo(name=attr_name, title=attr_name)
            entity_info[attr_name] = attr_info
            if name == 'prop':
                if not entity_info['_init'].body:
                    raise TypeError(f'can not define prop {entity_name}.{attr_name} without "body" attr')
                attr_info.body = entity_info['_init'].body
            if 'choices' in attrs:
                field = Choice
            elif attrs.get('cid', 'False') != 'False':
                field = Discriminator
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
                            set_later[v].append((reverse_name, entity_name))
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
                    entity_info['_init'].body = attr_info
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
    for v, lst in set_later.items():
        if v not in app_info:
            raise TypeError(f'foreign model {v} not found')
        fields = app_info[v]['_init'].fields
        for reverse_name, entity_name in lst:
            if reverse_name not in fields:
                fields[reverse_name] = Set(entity_name)


def expose_datebases(app: str, with_binding: bool = True, with_mapping: bool = True, app_info: Dict = None) -> Optional[Database]:
    if not with_binding:
        with_mapping = False

    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        return None

    if app_info is None:
        if app not in dbinfo:
            dbinfo[app] = ADict()
        app_info = dbinfo[app]
        for_reuse = False
    else:
        for_reuse = True

    schema = None
    all_db = []

    def start_element(name: str, attrs: dict):
        nonlocal schema, all_db, app_info
        if name != 'databases':
            kwargs = dict(attrs)
            db_name = kwargs.pop('name')
            if db_name == 'db':
                schema = kwargs.pop('schema', None)
            elif for_reuse:
                return
            if name == 'reuse':
                app = kwargs.pop('app')
                expose_datebases(app, app_info=app_info)
                all_db.append(app_info['db'].cls)
            else:
                kwargs['provider'] = name
                if with_binding:
                    db = Database(**kwargs)
                else:
                    db = Database()
                app_info[db_name] = DatabaseInfo(cls=db, kwargs=kwargs)
                all_db.append(db)

    parse_xml(file_name, start_element)

    if not for_reuse:
        expose_models(app_info['db'].cls, schema, app)

        # initialize entities
        for ent_name, ent in app_info.items():
            if isinstance(ent, ADict):
                ent_info = ent['_init']
                bases = []
                for base in ent_info.bases:
                    if isinstance(base, types.FunctionType):
                        bases.append(base())
                    else:
                        bases.append(base)
                ent_info.cls = type(ent_name, tuple(bases), ent_info.fields)

        # fill prop types
        for ent in app_info.values():
            if isinstance(ent, dict):
                for attr_info in ent.values():
                    if isinstance(attr_info, AttrInfo):
                        if isinstance(attr_info.type, str):
                            attr_info.type = app_info[attr_info.type]['_init'].cls

        if 'db' not in app_info:
            return None
    else:
        expose_models(app_info['db'].cls, schema, app, app_info)
        return None

    if with_mapping:
        for db in all_db:
            db.generate_mapping(create_tables=False, check_tables=False)

    return app_info['db'].cls


