from datetime import datetime

from pony.orm import Database, Required, Optional

db = Database()


class TestTable(db.Entity):
    Column1 = Optional(str, title='Колонка 1')
    Column2 = Optional(str, title='Строка')
    Column3 = Optional(int, title='Число')
    Column4 = Optional(float, title='Вещ. число')
    Column5 = Optional(datetime, title='Дата/время')

