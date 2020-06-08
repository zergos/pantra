from __future__ import annotations

import typing
import json
import os
import traceback
from datetime import datetime, time, timedelta, date
import xml.parsers.expat as expat
from decimal import Decimal
from uuid import UUID

from pony.orm import Database, Optional, Required, Set, LongStr, Json, StrArray, FloatArray, IntArray

from core.common import ADict
from core.defaults import APPS_PATH

if typing.TYPE_CHECKING:
    from typing import *

_type_map = {
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

_type_factory = {
    'bool': lambda s: s != 'False',
    'int': int,
    'float': float,
    'str': str,
    'bytes': bytes,
    'Decimal': Decimal,
    'datetime': lambda s: datetime.strptime(s, '%x %X'),
    'date': lambda s: datetime.strptime(s, '%x').date(),
    'time': lambda s: datetime.strptime(s, '%X').time(),
    'timedelta': lambda s: timedelta(seconds=float(s)),
    'UUID': str,
    'LongStr': str,
    'Json': json.loads,
}

_array_type_map = {
    'str': StrArray,
    'float': FloatArray,
    'int': IntArray,
}

dbinfo: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = ADict()  # app / entity / column / attr: value


def model_to_python(app: str):
    res = []
    in_python = False
    python = ''

    def start_element(name: str, attrs: dict):
        nonlocal res, in_python

        if name == 'entity':
            res.append('\n    class {}({}{}):'.format(attrs['name'], attrs.get('base', 'db.Entity'), ', '+attrs['mixin'] if 'mixin' in attrs else ''))
        elif name in ('attr', 'array'):
            attr_name = attrs['name']
            field = 'Optional' if attrs.get('required', 'False') == 'False' else 'Required'
            type = ''
            pars = []
            for a, v in attrs.items():
                if a == 'type':
                    type = v
                    if name == 'attr':
                        pars.append(type)
                elif a == 'default':
                    if type in ('int', 'float', 'Decimal', 'Json', 'bool'):
                        pars.append(f'{a}={v}')
                    else:
                        pars.append(f'{a}="{v}"')
                elif a not in ('name', 'title', 'width', 'required'):
                    pars.append(f'{a}="{v}"')
            if name == 'attr':
                res.append(f'    {attr_name} = {field}({", ".join(pars)})')
            else:
                res.append(f'    {attr_name} = {type.capitalize()}Array({", ".join(pars)})')
        elif name == 'set':
            attr_name = attrs['name']
            type = attrs['type']
            res.append(f'    {attr_name} = Set("{type}")')
        elif name == 'python':
            in_python = True

    def end_element(name: str):
        nonlocal in_python
        if name == 'python':
            in_python = False

    def char_data(data):
        nonlocal python
        if in_python:
            python += data

    p = expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data

    with open(os.path.join(APPS_PATH, app, 'data', 'models.xml'), 'rb') as f:
        p.ParseFile(f)

    return f'''# ---- {app} models for type checker
from __futures__ import annotations
import typing
if typing.TYPE_CHECKER:
    from pony.core import *
    db = Database()
''' + \
'\n'.join(f'    {line}' for line in python.splitlines()) + \
'\n'.join(f'    {line}' for line in res)


def expose_model(db: Database, app: str):
    global dbinfo

    file_name = os.path.join(APPS_PATH, app, 'data', 'models.xml')
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
            try:
                code = compile(python, file_name, 'exec')
                exec(code, locals)
            except:
                traceback.print_exc()

    def python_data(data):
        nonlocal python
        if in_python:
            python += data

    p = expat.ParserCreate()
    p.StartElementHandler = start_python
    p.EndElementHandler = end_python
    p.CharacterDataHandler = python_data

    with open(file_name, 'rt') as f:
        src = f.read()

    p.Parse(src, True)

    # expose entities
    entity_factory = None
    body = {}

    if app not in dbinfo:
        dbinfo[app] = ADict()
    app_info = dbinfo[app]
    entity_info = None

    def start_element(name: str, attrs: dict):
        nonlocal entity_factory, body, entity_info

        if name == 'entity':
            if 'base' in attrs:
                bases = [locals[b.strip()] for b in attrs['base'].split(',')]
            else:
                bases = [db.Entity]
            if 'mixin' in attrs:
                bases.append(locals[attrs['mixin']])
            entity_name = attrs['name']
            body = {}
            entity_factory = lambda: type(entity_name, bases, body)

            if entity_name not in app_info:
                app_info[entity_name] = ADict()
            entity_info = app_info[entity_name]

        elif name in ('attr', 'array'):
            attr_name = attrs['name']
            attr_info = ADict()
            entity_info[attr_name] = attr_info
            field = Optional if attrs.get('required', 'False') == 'False' else Required
            type = None
            type_name = ''
            kwargs = {}
            for a, v in attrs.items():
                if a == 'type':
                    type_name = v
                    if name == 'attr':
                        type = _type_map[v]
                    else:
                        field = _array_type_map[v]
                elif a == 'default':
                    kwargs[a] = _type_factory[type_name](v)
                elif a == 'title':
                    attr_info[a] = v
                elif a == 'width':
                    attr_info[a] = float(v)
                elif a not in ('name', 'required'):
                    kwargs[a] = v
            if name == 'attr':
                body[attr_name] = field(type, **kwargs)
            else:
                body[attr_name] = field(**kwargs)
        elif name == 'set':
            attr_name = attrs['name']
            type = _type_map['type']
            body[attr_name] = Set(type)

    def end_element(name: str):
        nonlocal entity_factory
        if name == 'entity':
            entity_factory()

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = None
    p.Parse(src, True)
