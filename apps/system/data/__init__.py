import uuid
import hashlib

from quazy.db import *
from quazy.db_types import *

_SCHEMA_ = "system"


class User(DBTable):
    _title_ = "user"
    name: str
    password: str | None
    salt: str | None
    email: str | None
    created_at: datetime = DBField(default=datetime.now, ux=UX('created'))
    is_admin: bool = DBField(default=False, ux=UX('A', width=3))
    enabled: bool = DBField(default=False, ux=UX('E', width=3))
    apps: ManyToMany['App']

    def _view(self, s):
        return s.name

    def set_password(self, password):
        self.salt = uuid.uuid4().hex
        self.password = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()

    def check_password(self, password):
        check = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()
        return check == self.password


class App(DBTable):
    name: str
    title: str | None
    users: ManyToMany[User]

    def _view(self, s):
        return s.name


class Document(DBTable):
    prefix: str = DBField(default="", ux=UX(width=2))
    number: int = DBField(ux=UX(width=6))
    date: datetime = DBField(default=datetime.now)
    body: dict = DBField(body=True)

    class DocumentLine(DBTable):
        pos: int = DBField(ux=UX(width=5))
        data: dict = DBField(body=True)


class Catalog(DBTable):
    prefix: str = DBField(default="", ux=UX(width=2))
    number: int = DBField(ux=UX(width=6))
    name: str | None
    body: dict = DBField(body=True)

    def _before_update(self, db: DBFactory):
        if not self.number:
            check = db.query(Catalog).filter(prefix=self.prefix)
            if not check.exists():
                self.number = 1
            else:
                max = db.query(Catalog)\
                    .filter(prefix=self.prefix)\
                    .exclude(pk=self)\
                    .fetch_max('number')
                self.number = max and max + 1 or 1
        else:
            look_up = db.get(Catalog, prefix=self.prefix, number=self.number)
            if look_up != self:
                raise ValueError(f'Catalog number {self.number} is not unique')


from pantra.models import expose_database
db = expose_database('system')
db.use_module()
