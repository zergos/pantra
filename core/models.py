from __future__ import annotations

import types
import typing
import json
import os
import traceback
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field as dc_field
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

__all__ = ['dbinfo', 'expose_datebases', 'expose_to_pony', 'expose_to_django']

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
    'bool': 'models.BooleanField',
    'int': 'models.IntegerField',
    'float': 'models.FloatField',
    'str': 'models.TextField',
    'bytes': 'models.BinaryField',
    'Decimal': 'models.DecimalField',
    'datetime': 'models.DateTimeField',
    'date': 'models.DateField',
    'time': 'models.TimeField',
    'timedelta': 'models.DurationField',
    'UUID': 'models.UUIDField',
    'LongStr': 'models.TextField',
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


@dataclass
class EntityInfo:
    cls: type  = dc_field(init=False)
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


def _parse_xml(file_name, start_handler, end_handler=None, content_handler=None, parser=None):
    p = parser or expat.ParserCreate()
    p.StartElementHandler = start_handler
    p.EndElementHandler = end_handler
    p.CharacterDataHandler = content_handler
    try:
        with open(file_name, 'rt') as f:
            src = f.read()
            p.Parse(src, True)
    except expat.ExpatError:
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

    entity_name = ''
    lines = []

    def start_element(name: str, attrs: dict):
        nonlocal in_python, set_later, entity_name, lines

        if name == 'entity':
            lines = []
            entity_name = attrs['name']
            models[entity_name] = lines
            lines.append('\n    class {}({}{}):'.format(entity_name, attrs.get('base', 'EntityMeta'), ', '+attrs['mixin'] if 'mixin' in attrs else ''))
            if 'display' in attrs:
                lines.append(f'    def __str__(self):\n            return {attrs["display"]}')
        elif name in ('attr', 'array', 'prop'):
            attr_name = attrs['name']
            if 'choices' in attrs:
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
                                reverse_name = f'{entity_name.lower()}s'
                                pars.append(f"reverse='{reverse_name}'")
                            else:
                                reverse_name = attrs['reverse']
                            set_later[t].append((reverse_name, entity_name))
                elif a == 'default':
                    if t in ('int', 'float', 'Decimal', 'Json', 'bool'):
                        pars.append(f'{a}={v}')
                    else:
                        pars.append(f"{a}='{v}'")
                elif a == 'eval':
                    pars.append(f"default='{v}'")
                elif a == 'choices':
                    pars.append(f"{a}=v")
                elif a == 'index':
                    if attrs['index'] != 'False':
                        pars.append('index=True')
                elif a in ('precision', 'sql_default', 'unique', 'reverse'):
                    pars.append(f"{a}='{v}'")
            if name == 'attr':
                lines.append(f'    {attr_name} = {field}({", ".join(pars)})')
            elif name == 'array':
                lines.append(f'    {attr_name} = {t.capitalize()}Array({", ".join(pars)})')
            elif name == 'prop':
                lines.extend(f'''    @property
    def {attr_name}(self):
        return self.body['{attr_name}']
    @{attr_name}.setter
    def {attr_name}(self, value):
        self.body['{attr_name}'] = value'''.splitlines())
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

    return models, set_later, python.strip()


def expose_to_pony(app: str):

    models, set_later, python = _pony_collect_models(app)

    # add attrs with refs
    for model_name, attrs in set_later.items():
        for attr_name, entity_name in attrs:
            attr_text = f'    {attr_name} = Set("{entity_name}")'
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
if typing.TYPE_CHECKING:
    from datetime import datetime, time, timedelta, date
    from decimal import Decimal
    from uuid import UUID
    from pony.orm import *
    from pony.orm.core import EntityMeta
    from core.dbtools import Choice

'''.splitlines()

    body.extend([f'    {line}' for line in python.splitlines()])
    for lines in models.values():
        body.append('')
        body.extend([f'    {line}' for line in lines])

    body.append('')
    body.append('    class DB:')
    for model_name in models.keys():
        body.append(f'        {model_name}: {model_name}')
    body.append('')

    with open(os.path.join(APPS_PATH, app, 'data', 'pony.py'), 'wt') as f:
        f.write('\n'.join(body))


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
    _parse_xml(file_name, start_python, end_python, python_data, parser=p)

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
                        if v in _type_map:
                            t = _type_map[v]
                            attr_info.type = t
                        else:
                            t = v
                            reverse_name = attrs.get('reverse', f'{entity_name.lower()}s')
                            set_later[v].append((reverse_name, entity_name))
                            attr_info.type = t
                    else:
                        field = _array_type_map[v]
                        attr_info.type = list
                elif a == 'default':
                    kwargs[a] = _type_factory[type_name](v)
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

    _parse_xml(file_name, start_element)

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

    _parse_xml(file_name, start_element)

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


@dataclass
class ModelInfo:
    name: str
    cap: str
    fields: OrderedDict[str, 'FieldInfo']
    base: Optional['ModelInfo']
    has_cid: bool
    managed: bool
    schema: str


@dataclass
class FieldInfo:
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
        nonlocal db, schema, models
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
                if schema:
                    db['OPTIONS'] = {'options': f'-c search_path={schema},public'}
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
                elif _schema:
                    db['OPTIONS'] = {'options': f'-c search_path={schema},public'}

    _parse_xml(file_name, start_element)

    # parse models

    file_name = os.path.join(APPS_PATH, app, 'data', 'models.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    actual_model: ModelInfo
    actual_fields: OrderedDict[str, FieldInfo]
    first_entity = True

    def start_element(name: str, attrs: dict):
        nonlocal models, actual_model, actual_fields, first_entity

        if name == 'entity':
            model_name = attrs['name']
            if 'base' in attrs:
                actual_model = models[attrs['base']]
                while actual_model.base:
                    actual_model = actual_model.base
                actual_fields = actual_model.fields
                if not actual_model.has_cid:
                    actual_fields['classtype'] = FieldInfo('models.TextField(db_index=True)', None, {})
                    actual_fields.move_to_end('classtype', last=False)
                    actual_model.managed = True
                    actual_model.schema = schema
            else:
                if first_entity:
                    pre_cap = f'# ---- rendered from {app} ----\n'
                    first_entity = False
                else:
                    pre_cap = ''
                cap = f'{pre_cap}class {model_name}(models.Model):'
                actual_fields = OrderedDict()
                actual_model = ModelInfo(model_name, cap, actual_fields, None, False, managed, schema)
                models[model_name] = actual_model

        elif name in ('attr', 'array'):
            attr_name = attrs['name']
            pars = []
            if attrs.get('cid', 'False') != 'False' or attrs.get('required', 'False') != 'False':
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
                        field = 'models.ForeignKey'
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
                elif a == 'eval':
                    if v == 'datetime.now':
                        pars.append(f'auto_now=True')
                    else:
                        pars.append(f'default={v}')
                elif a == 'unique':
                    pars.append(f'unique={attrs.get("unique", "False")!="False"}')
                elif a == 'precision':
                    pars.append(f'precision={v}')
            if name != 'array':
                actual_fields[attr_name] = FieldInfo(f'{field}({", ".join(pars)})', None, attrs)
            else:
                actual_fields[attr_name] = FieldInfo(f'ArrayField({field}({", ".join(pars)}))', None, attrs)
        elif name == 'set':
            attr_name = attrs['name']
            t = attrs['type']
            # check refs later
            actual_fields[attr_name] = FieldInfo('', lambda: models[t], attrs)

    _parse_xml(file_name, start_element)

    # collect refs
    for model_name, model in list(models.items()):
        for field_name, field in list(model.fields.items()):
            if field.ref and not field.cap:
                # check many to many
                has_back = False
                for ff_name, ff in field.ref().fields.items():
                    if ff.ref and ff.ref() == model:
                        has_back = True
                        tmodel_name = f'{model_name}_{field.ref().name}'
                        field.cap = f"models.ManyToManyField('{model_name}', " \
                                    f"through='{tmodel_name}')"
                                    #f"through_fields=('{field.ref().name.lower()}', '{model_name.lower()}'))"
                        del field.ref().fields[ff_name]
                        tmanaged = model.managed or field.ref().managed
                        if not schema:
                            db_table = tmodel_name.lower()
                        else:
                            db_table = f'{schema}"."{tmodel_name.lower()}'
                        cap = f'''class {tmodel_name}(models.Model):
    class Meta:
        db_table = '{db_table}'
        managed = {tmanaged}
'''
                        fields = {
                            model_name.lower(): FieldInfo(f"models.ForeignKey('{model_name}', on_delete=models.CASCADE, db_column='{model_name.lower()}')", None, {}),
                            field.ref().name.lower(): FieldInfo(f"models.ForeignKey('{field.ref().name}', on_delete=models.CASCADE, db_column='{field.ref().name.lower()}')", None, {})
                        }
                        models[tmodel_name] = ModelInfo(tmodel_name, cap, fields, None, False, managed, schema)
                        break
                if not has_back:
                    del model.fields[field_name]

    return db, schema, models


def expose_to_django(app: str, gen_settings_file: bool = False):
    base_path = os.path.join(APPS_PATH, app)
    data_path = os.path.join(base_path, 'data')

    db, schema, models = _django_collect_models(app, True)

    if gen_settings_file:
        settings = f'''# auto-generated for migration purposes
BASE_DIR = {base_path}
SECRET_KEY = '09=ce-ql+9hoo0*xrn+dzksejsnn4qfq$e1fq%pwx8agrm_%z8'
DEBUG = False
INSTALLED_APPS = ['data']
USE_TZ = False
DATABASES = {{'default': {db}}}\n'''

        with open(os.path.join(data_path, 'settings.py'), "wt") as f:
            f.write(settings)

    settings = dict(
        BASE_DIR=base_path,
        SECRET_KEY='09=ce-ql+9hoo0*xrn+dzksejsnn4qfq$e1fq%pwx8agrm_%z8',
        DEBUG=False,
        INSTALLED_APPS=['.'.join(['apps', app, 'data', 'app', 'Config'])],
        USE_TZ=False,
        LOGGING_CONFIG=None,
        DATABASES={'default': db}
    )

    init = f'''# auto-generated for migration purposes
# we need to specify app name via label to make migrations work, and it should be separate file
from django.apps import AppConfig
class Config(AppConfig):
    name = 'apps.{app}.data'
    label = '{app}'
    '''

    with open(os.path.join(data_path, 'app.py'), "wt") as f:
        f.write(init)

    body = '''# auto-generated for migration purposes
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

'''.splitlines()

    for model in models.values():
        body.append('')
        body.append(model.cap)
        body.append('    class Meta:')
        if not model.schema:
            db_table = model.name.lower()
        else:
            db_table = f'{model.schema}"."{model.name.lower()}'
        body.append(f"        db_table = '{db_table}'")
        body.append(f'        managed = {model.managed}')
        for field_name, field in model.fields.items():
            body.append(f'    {field_name} = {field.cap}')
        body.append('')

    with open(os.path.join(data_path, 'models.py'), "wt") as f:
        f.write('\n'.join(body))

    return settings
