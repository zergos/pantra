import hashlib
import uuid
from datetime import datetime

from pony.orm import Database, Required, Optional, Set

db = Database()


class User(db.Entity):
    name = Required(str)
    password = Optional(str)
    salt = Optional(str)
    email = Required(str, unique=True)
    created_at = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    is_admin = Required(bool)

    apps = Set('App')

    def set_password(self, password):
        self.salt = uuid.uuid4().hex
        self.password = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()

    def check_password(self, password):
        check = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()
        return check == self.password


class App(db.Entity):
    name = Required(str)
    title = Required(str)
    users = Set(User)


class TestTable(db.Entity):
    Column1 = Optional(str, title='Колонка 1')
    Column2 = Optional(str, title='Строка')
    Column3 = Optional(int, title='Число')
    Column4 = Optional(float, title='Вещ. число')
    Column5 = Optional(datetime, title='Дата/время')

