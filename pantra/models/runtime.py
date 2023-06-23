from __future__ import annotations

import typing
import os
from dataclasses import dataclass, field as dc_field

from quazy import DBFactory

from pantra.common import ADict
from pantra.defaults import APPS_PATH
from .parser import parse_xml

if typing.TYPE_CHECKING:
    from typing import *


@dataclass
class DatabaseInfo:
    factory: DBFactory = dc_field(default=None)
    schema: str = dc_field(default_factory=str)
    kwargs: Dict[str, str] = dc_field(default_factory=dict)


dbinfo: Dict[str, Dict[str, DatabaseInfo]] = ADict()  # app / db / DatabaseInfo


def expose_databases(app: str, app_info: Dict[str, DatabaseInfo] = None) -> Optional[DBFactory]:
    if not app_info and app in dbinfo:
        app_info = dbinfo[app]
        if 'db' in app_info:
            return app_info['db'].factory
        else:
            return None

    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        return None

    if app_info is None:
        if app not in dbinfo:
            dbinfo[app] = {}
        app_info = dbinfo[app]

    all_db = []

    def start_element(name: str, attrs: dict):
        nonlocal all_db, app_info
        if name != 'databases':
            kwargs = dict(attrs)
            db_name = kwargs.pop('name')
            schema = kwargs.pop('schema', '')
            if name == 'reuse':
                parent_app = kwargs.pop('app')
                expose_databases(parent_app, app_info=app_info)
                app_info[db_name].schema = schema  # override schema
                all_db.append(app_info[db_name].factory)
            else:
                db: DBFactory = getattr(DBFactory, name)(**kwargs)
                kwargs['provider'] = name
                app_info[db_name] = DatabaseInfo(db, schema=schema, kwargs=kwargs)
                all_db.append(db)

    parse_xml(file_name, start_element)

    if 'db' not in app_info:
        return None

    return app_info['db'].factory
