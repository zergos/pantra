from __future__ import annotations

import typing
import json
import os
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
import xml.parsers.expat as expat
from decimal import Decimal
from uuid import UUID

from pony.orm import Database, Optional, Required, Discriminator, Set, LongStr, Json, StrArray, FloatArray, IntArray
from core.dbtools import Choice

from core.common import ADict
from core.defaults import APPS_PATH

if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['expose_datebases', 'dbinfo']

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

_django_type_map = {
    'bool': 'BooleanField',
    'int': 'IntegerField',
    'float': 'FloatField',
    'str': 'TextField',
    'bytes': 'BinaryField',
    'Decimal': 'DecimalField',
    'datetime': 'DateTimeField',
    'date': 'DateField',
    'time': 'TimeField',
    'timedelta': 'DurationField',
    'UUID': 'UUIDField',
    'LongStr': 'TextField',
    'Json': 'JSONField',
}

_type_factory = {
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

_array_type_map = {
    'str': StrArray,
    'float': FloatArray,
    'int': IntArray,
}


@dataclass
class DatabaseInfo:
    cls: Database
    kwargs: Dict[str, Any]
    parent: Database


dbinfo: Dict[str, Dict[str, Union[Dict[str, Dict[str, Any]], DatabaseInfo]]] = ADict()  # app / entity+db / column / attr: value


def _parse_xml(file_name, start_handler, end_handler=None, content_handler=None, parser=None):
    p = parser or expat.ParserCreate()
    p.StartElementHandler = start_handler
    p.EndElementHandler = end_handler
    p.CharacterDataHandler = content_handler
    try:
        with open(file_name, 'rt') as f:
            src = f.read()
            p.Parse(src, True)
    except:
        traceback.print_exc(limit=-1)
        print(src.splitlines()[p.ErrorLineNumber-1])
        print(f'{file_name}> {p.ErrorLineNumber}:{p.ErrorColumnNumber}')


def _pony_collect_models(app: str) -> Tuple[Dict, Dict, str]:
    # parse referred models
    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    python = ''

    models: Dict[str, List[str]] = {}  # entity name / lines
    set_later: Dict[str, List[str]] = defaultdict(list)  # entity name / attr

    def start_element(name: str, attrs: dict):
        nonlocal python, models, set_later
        if name == 'reuse' and attrs['name'] == 'db':
            _models, _set_later, _python = _pony_collect_models(attrs['app'])
            models.update(_models)
            set_later.update(_set_later)
            python += _python

    _parse_xml(file_name, start_element)

    # parse current models
    file_name = os.path.join(APPS_PATH, app, 'data', 'models.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    in_python = False

    model_name = ''
    lines = []

    def start_element(name: str, attrs: dict):
        nonlocal in_python, set_later, model_name, lines

        if name == 'entity':
            lines = []
            models[attrs['name']] = lines
            lines.append('\n    class {}({}{}):'.format(attrs['name'], attrs.get('base', 'db.Entity'), ', '+attrs['mixin'] if 'mixin' in attrs else ''))
        elif name in ('attr', 'array', 'choice'):
            attr_name = attrs['name']
            if name == 'choice':
                field = 'Choice'
            elif attrs.get('cid', 'False') != 'False':
                field = 'Discriminator'
            else:
                field = 'Optional' if attrs.get('required', 'False') == 'False' else 'Required'
            t = ''
            pars = []
            for a, v in attrs.items():
                if a == 'type':
                    t = v
                    if name == 'attr':
                        pars.append(t)
                        if t not in _type_map:
                            if 'reverse' not in attrs:
                                reverse_name = f'{attr_name}s'
                                pars.append(f"reverse='{reverse_name}'")
                            else:
                                reverse_name = attrs['reverse']
                            set_later[t].append(reverse_name)
                elif a == 'default':
                    if t in ('int', 'float', 'Decimal', 'Json', 'bool'):
                        pars.append(f'{a}={v}')
                    else:
                        pars.append(f"{a}='{v}'")
                elif a not in ('name', 'title', 'width', 'required', 'choices'):
                    pars.append(f"{a}='{v}'")
            if name != 'array':
                lines.append(f'    {attr_name} = {field}({", ".join(pars)})')
            else:
                lines.append(f'    {attr_name} = {t.capitalize()}Array({", ".join(pars)})')
        elif name == 'set':
            attr_name = attrs['name']
            t = attrs['type']
            lines.append(f'    {attr_name} = Set("{t}")')
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

    _parse_xml(file_name, start_element, end_element, char_data)

    return models, set_later, python


def models_to_python(app: str):

    models, set_later, python = _pony_collect_models(app)

    # add attrs with refs
    for model_name, attrs in set_later:
        for attr in attrs:
            attr_text = f'    {attr} = Set("{model_name}")'
            found = False
            for line in reversed(models[model_name]):
                if attr_text in line:
                    found = True
                    break
            if not found:
                models[model_name].append(attr_text)

    body: List = f'''# ---- auto-generated {app} models for type checker
from __future__ import annotations
import typing
if typing.TYPE_CHECKER:
    from datetime import datetime, time, timedelta, date
    from decimal import Decimal
    from uuid import UUID
    from pony.core import *
    from core.dbtools import Choice

    db = Database()
'''.splitlines()

    body.extend([f'    {line}' for line in python.splitlines()])
    for lines in models.values():
        body.extend([f'    {line}' for line in lines])

    with open(os.path.join(APPS_PATH, app, 'data', 'pony.py'), 'wt') as f:
        f.write('\n'.join(body))


def expose_models(db: Database, schema: Optional[str], app: str):
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
    _parse_xml(file_name, start_python, end_python, python_data, parser=p)

    # expose entities
    entity_factory = None
    body = {}

    if app not in dbinfo:
        dbinfo[app] = ADict()
    app_info = dbinfo[app]
    entity_name = ''
    entity_info = None

    def start_element(name: str, attrs: dict):
        nonlocal entity_factory, body, entity_name, entity_info

        if name == 'entity':
            actual_db_info = app_info['db']
            if 'base' in attrs:
                bases = [locals[b.strip()] for b in attrs['base'].split(',')]
            elif 'db' in attrs:
                actual_db_info = app_info[attrs['db']]
                bases = [actual_db_info.cls.Entity]
            else:
                bases = [db.Entity]
            if 'mixin' in attrs:
                bases.append(locals[attrs['mixin']])
            entity_name = attrs['name']
            body = {}
            if schema and 'db' not in attrs:
                body['_table_'] = (schema, entity_name.lower())
            if 'cid' in attrs:
                body['_discriminator_'] = int(attrs['cid'])
            entity_factory = lambda: type(entity_name, tuple(bases), body)

            if entity_name not in app_info:
                app_info[entity_name] = ADict({'db': actual_db_info.cls})
            entity_info = app_info[entity_name]

        elif name in ('attr', 'array', 'choice'):
            attr_name = attrs['name']
            attr_info = ADict()
            entity_info[attr_name] = attr_info
            if name == 'choice':
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
                        if v in _type_map:
                            t = _type_map[v]
                        else:
                            if v not in app_info:
                                raise TypeError('{v} type/entity not found')
                            reverse_name = attrs.get('reverse', f'{entity_name.lower()}s')
                            rev_entity = app_info[v]['_cls']
                            if not hasattr(rev_entity, reverse_name):
                                rev_entity.__dict__[reverse_name] = Set(entity_name)
                    else:
                        field = _array_type_map[v]
                elif a == 'default':
                    kwargs[a] = _type_factory[type_name](v)
                elif a == 'title':
                    attr_info[a] = v
                elif a == 'width':
                    attr_info[a] = float(v)
                elif a == 'choices':
                    attr_info[a] = locals[v]
                elif a not in ('name', 'required', 'cid'):
                    kwargs[a] = v
            if name != 'array':
                body[attr_name] = field(t, **kwargs)
            else:
                body[attr_name] = field(**kwargs)
        elif name == 'set':
            attr_name = attrs['name']
            body[attr_name] = Set(attrs['type'])

    def end_element(name: str):
        nonlocal entity_factory
        if name == 'entity':
            app_info['_cls'] = entity_factory()

    _parse_xml(file_name, start_element, end_element)


def expose_datebases(app: str, with_binding: bool = True, with_mapping: bool = True) -> Optional[Database]:
    if not with_binding:
        with_mapping = False

    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        return None

    if app not in dbinfo:
        dbinfo[app] = ADict()
    app_info = dbinfo[app]

    schema = None
    all_db = []

    def start_element(name: str, attrs: dict):
        nonlocal schema, all_db
        if name != 'databases':
            kwargs = dict(attrs)
            db_name = kwargs.pop('name')
            if db_name == 'db':
                schema = kwargs.pop('schema', None)
            if name == 'reuse':
                app = kwargs.pop('app')
                if app not in dbinfo:
                    expose_datebases(app, with_binding, with_mapping)
                if with_binding:
                    db = Database(**dbinfo[app]['db'].kwargs)
                else:
                    db = Database()
                kwargs.update(dbinfo[app]['db'].kwargs)
                parent = dbinfo[app]['db'].cls
            else:
                kwargs['provider'] = name
                if with_binding:
                    db = Database(**kwargs)
                else:
                    db = Database()
                parent = None
            all_db.append(db)
            app_info[db_name] = DatabaseInfo(cls=db, kwargs=kwargs, parent=parent)

    _parse_xml(file_name, start_element)

    if 'db' not in app_info:
        return None

    expose_models(app_info['db'].cls, schema, app)

    if with_mapping:
        for db in all_db:
            db.generate_mapping(create_tables=False)

    return app_info['db'].cls


@dataclass
class ModelInfo:
    name: str
    cap: str
    fields: OrderedDict[str, 'FieldInfo']
    base: Optional['ModelInfo']
    has_cid: bool


class FieldInfo(typing.NamedTuple):
    cap: str
    ref: Optional[Callable[[],'ModelInfo']]
    attrs: Dict[str, Any]


def _django_collect_models(app: str, managed: bool) -> Tuple[Dict[str, str], str, Dict[str, ModelInfo]]:
    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    # parse default database properties
    db = {}
    schema = ''
    models: Dict[str, ModelInfo] = {}

    def start_element(name: str, attrs: dict):
        nonlocal db, schema
        if name != 'databases':
            if attrs['name'] != 'db':
                return
            schema = attrs.get('schema', '')
            if name in ['postgres', 'cockroach']:
                db = {
                    'ENGINE': 'django.db.backends.postgresql_psycopg2' if name == 'postgres' else 'django_cockroachdb',
                    'NAME': attrs['database'],
                    'USER': attrs.get('user', ''),
                    'PASSWORD': attrs.get('password', ''),
                    'HOST': attrs.get('host', ''),
                    'PORT': attrs.get('port', ''),
                }
                if 'schema' in attrs:
                    db['OPTIONS'] = {'options': f'-c search_path={attrs["schema"]},public'}
            elif name == 'sqlite':
                db = {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': attrs['filename'],
                }
            elif name == 'mysql':
                db = {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': attrs['db'],
                    'USER': attrs.get('user', ''),
                    'PASSWORD': attrs.get('passwd', ''),
                    'HOST': attrs.get('host', ''),
                    'PORT': attrs.get('port', ''),
                }
            elif name == 'oracle':
                db = {
                    'ENGINE': 'django.db.backends.oracle',
                    'NAME': attrs['dsn'],
                    'USER': attrs.get('user', ''),
                    'PASSWORD': attrs.get('passwd', ''),
                }
            elif name == 'reuse':
                db, _schema, models = _django_collect_models(attrs['app'], False)
                if not schema:
                    schema = _schema

    _parse_xml(file_name, start_element)

    # parse models

    file_name = os.path.join(APPS_PATH, app, 'data', 'models.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    actual_model: ModelInfo
    actual_fields: OrderedDict[str, FieldInfo]

    def start_element(name: str, attrs: dict):
        nonlocal models, actual_model, actual_fields

        if name == 'entity':
            model_name = attrs['name']
            if 'base' in attrs:
                actual_model = models[attrs['base']]
                while actual_model.base:
                    actual_model = actual_model.base
                actual_fields = actual_model.fields
                if not actual_model.has_cid:
                    actual_fields['classtype'] = FieldInfo('TextField(null=True)', None, {})
                    actual_fields.move_to_end('classtype', last=False)
            else:
                if not schema:
                    db_table = model_name.lower()
                else:
                    db_table = f'{schema}\".\"{model_name.lower()}'
                cap = f'''class {model_name}(models.Model):
    class Meta:
        db_table = {db_table}
        managed = {managed}
    '''
                actual_fields = OrderedDict()
                actual_model = ModelInfo(model_name, cap, actual_fields, None, False)
                models[model_name] = actual_model

        elif name in ('attr', 'array', 'choice'):
            attr_name = attrs['name']
            pars = []
            if name == 'choice' or attrs.get('cid', 'False') != 'False' or attrs.get('required', 'False') != 'False':
                required = True
            else:
                pars.append('null=True')
                required = False
            if attrs.get('cid', 'False') != 'False':
                actual_model.has_cid = True
            t = ''
            field = ''
            for a, v in attrs.items():
                if a == 'type':
                    t = v
                    if v in _django_type_map:
                        field = _django_type_map[v]
                    else:
                        field = 'ForeignKey'
                        pars.insert(0, f"'{v}'")
                        if required:
                            pars.insert(1, 'on_delete=models.CASCADE')
                        else:
                            pars.insert(1, 'on_delete=models.SET_NULL')
                        pars.append(f"db_column='{attr_name}'")
                elif a == 'default':
                    if t in ('int', 'float', 'Decimal', 'Json', 'bool'):
                        pars.append(f'{a}={v}')
                    else:
                        pars.append(f'{a}="{v}"')
                elif a == 'unique':
                    pars.append(f'unique={attrs.get("unique", "False")!="False"}')
                elif a == 'precision':
                    pars.append(f'precision={v}')
            if name != 'array':
                models[attr_name] = FieldInfo(f'{field}({", ".join(pars)})', None, attrs)
            else:
                models[attr_name] = FieldInfo(f'ArrayField({field}({", ".join(pars)}))', None, attrs)
        elif name == 'set':
            attr_name = attrs['name']
            t = attrs['type']
            # check refs later
            models[attr_name] = FieldInfo('', lambda: models[t], attrs)

    _parse_xml(file_name, start_element)

    # collect refs
    for model_name, model in models.items():
        for field_name, field in list(model.fields.items()):
            if field.ref and not field.cap:
                # check many to many
                has_back = False
                for ff_name, ff in field.ref().fields.items():
                    if ff.ref and ff.ref() == model:
                        has_back = True
                        field.cap = f"ManyToManyField('{model_name}', db_table='{model_name.lower()}_{field_name}', through_fields=('{model_name.lower()}', '{field.ref().name.lower()}'))"
                        del field.ref().fields[ff_name]
                        break
                if not has_back:
                    del model.fields[field_name]

    return db, schema, models


def expose_to_django(app: str):
    base_path = os.path.join(APPS_PATH, app)
    data_path = os.path.join(base_path, 'data')

    db, schema, models = _django_collect_models(app, True)

    settings = f'''# auto-generated for migration purposes
BASE_DIR = {base_path}
SECRET_KEY = '09=ce-ql+9hoo0*xrn+dzksejsnn4qfq$e1fq%pwx8agrm_%z8'
DEBUG = False
INSTALLED_APPS = ['data']
USE_TZ = False
DATABASES = {{'default': {db}}}\n'''

    with open(os.path.join(data_path, 'settings.py'), "wt") as f:
        f.write(settings)

    body = '''# auto-generated for migration purposes
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

'''.splitlines()

    for model in models.values():
        body.append(model.cap)
        for field_name, field in model.fields.items():
            body.append(f'    {field_name} = {field.cap}')
        body.append('')

    with open(os.path.join(data_path, 'models.py'), "wt") as f:
        f.write('\n'.join(body))


