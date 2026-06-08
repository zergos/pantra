from __future__ import annotations

import copy
import typing
from dataclasses import dataclass, field as dc_field

from ..settings import config
from .parser import parse_xml

if typing.TYPE_CHECKING:
    from typing import *
    try:
        from quazy import DBFactory
    except ImportError:
        pass


@dataclass
class DatabaseInfo:
    factory: DBFactory = None
    schema: str = ""
    kwargs: Dict[str, str] = dc_field(default_factory=dict)


dbinfo: dict[str, dict[str, DatabaseInfo]] = {}  # app / db / DatabaseInfo


def expose_database(app: str, db_name: str = 'db') -> Union[DBFactory | None]:
    try:
        from quazy import DBFactory
    except ImportError as e:
        raise RuntimeError("`quazydb` is not installed") from e

    if app in dbinfo:
        app_info = dbinfo[app]
        if db_name in app_info:
            return app_info[db_name].factory
        else:
            return None

    file_name = config.APPS_PATH / app / 'data' / 'databases.xml'
    if not file_name.exists():
        return None

    if app not in dbinfo:
        dbinfo[app] = {}
    app_info: dict[str, DatabaseInfo] = dbinfo[app]

    def start_element(name: str, attrs: dict):
        nonlocal app_info
        if name != 'databases':
            kwargs = dict(attrs)
            db_name = kwargs.pop('name')
            schema = kwargs.pop('schema', '')
            if name == 'reuse':
                parent_app = kwargs.pop('app')
                expose_database(parent_app)
                db_info = copy.copy(dbinfo[parent_app]['db'])
                app_info[db_name] = db_info
                db_info.schema = schema  # override schema
                db_info.factory.bind_module(f'apps.{app}.data')
            else:
                db: DBFactory = getattr(DBFactory, name)(**kwargs)
                kwargs['provider'] = name
                app_info[db_name] = DatabaseInfo(db, schema=schema, kwargs=kwargs)
                db.bind_module(f'apps.{app}.data')

    parse_xml(file_name, start_element)

    if db_name not in app_info:
        return None

    return app_info['db'].factory
