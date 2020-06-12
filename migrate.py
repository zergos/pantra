#!/usr/bin/env python
#import db.models
from datetime import datetime

from pony.orm import *
import core.defaults as settings

db = Database()

class TestTable2(db.Entity):
    Column1 = Optional(str, title='Колонка 1')
    Column2 = Optional(str, title='Строка')
    Column3 = Optional(int, title='Число')
    Column4 = Optional(float, title='Вещ. число')
    Column5 = Optional(datetime, title='Дата/время')

db.models.db.migrate(migration_dir=settings.MIGRATION_PATH, **settings.DB_PARAMS)
