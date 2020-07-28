from __future__ import annotations

import typing
import os
from collections import OrderedDict
from dataclasses import dataclass

from core.defaults import *

from .parser import parse_xml

if typing.TYPE_CHECKING:
    from typing import *


django_type_map = {
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

    parse_xml(file_name, start_element)

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
                    if v in django_type_map:
                        field = django_type_map[v]
                    else:
                        field = 'models.ForeignKey'
                        # TODO: foreign schema usage
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

    parse_xml(file_name, start_element)

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


# monkey patch: renaming table within schema
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.ddl_references import Statement


def alter_db_table(self, model, old_db_table, new_db_table):
    """Rename the table a model points to."""
    if (old_db_table == new_db_table or
        (self.connection.features.ignores_table_name_case and
            old_db_table.lower() == new_db_table.lower())):
        return
    if '"' in new_db_table: new_db_table = new_db_table.split('"')[-1]  # <-- here
    self.execute(self.sql_rename_table % {
        "old_table": self.quote_name(old_db_table),
        "new_table": self.quote_name(new_db_table),
    })
    # Rename all references to the old table name.
    for sql in self.deferred_sql:
        if isinstance(sql, Statement):
            sql.rename_table_references(old_db_table, new_db_table)
BaseDatabaseSchemaEditor.alter_db_table = alter_db_table
