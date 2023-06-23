import uuid
import hashlib

from quazy import *

_SCHEMA_ = "system"


class User(DBTable):
    name: str
    password: Optional[str]
    salt: Optional[str]
    email: Optional[str]
    created_at: datetime = DBField(default=datetime.now, ux=UX('created'))
    is_admin: bool = DBField(default=False, ux=UX('A', width=3))
    enabled: bool = DBField(default=False, ux=UX('E', width=3))
    apps: Many['App']

    def __view__(self, s: DBScheme):
        return s.name

    def set_password(self, password):
        self.salt = uuid.uuid4().hex
        self.password = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()

    def check_password(self, password):
        check = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()
        return check == self.password


class App(DBTable):
    name: str
    title: Optional[str]
    users: Many[User]

    def __view__(self, s: DBScheme):
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
    name: Optional[str]
    body: dict = DBField(body=True)

    def _before_update(self, db: DBFactory):
        if not self.number:
            amount = db.query(Catalog).filter(lambda s: s.prefix == self.prefix).fetch_count()
            if amount == 0:
                self.number = 1
            else:
                max = db.query(Catalog).filter(lambda s: (s.prefix == self.prefix) & (s.id != self.id)).fetch_max()
                self.number = max and max + 1 or 1
        else:
            look_up = db.lookup(Catalog, prefix=self.prefix, number=self.number)
            if look_up.id != self.id:
                raise ValueError(f'Catalog number {self.number} is not unique')


from pantra.models import expose_databases
db = expose_databases('system')
db.use_module()
