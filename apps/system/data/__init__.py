import uuid
import hashlib

from quazy import *

from pantra.ctx import *

_SCHEMA_ = "system"

class Document(DBTable):
    _lookup_field_ = 'number'
    _meta_ = True
    id: int = DBField(pk=True, ux=UX(blank=True, hidden=True))

    number: int = DBField(ux=UX(width=6, blank=True))
    date: datetime = DBField(default=datetime.now)

    def __str__(self):
        return f'{_(type(self).__name__)} - {self.number} - {session.locale.datetime(self.date)}'

    class Row(DBTable):
        _meta_ = True
        pos: int = DBField(ux=UX(width=5))
        data: FieldBody


class Catalog(DBTable):
    _lookup_field_ = 'name'
    _meta_ = True
    id: int = DBField(pk=True, ux=UX(blank=True, hidden=True))

    number: int = DBField(ux=UX(width=6, blank=True))
    name: str | None

    def __str__(self):
        return self.name

    @classmethod
    def _view_(cls, item: DBQueryField[typing.Self]):
        return item.name

    def check_number(self, db: DBFactory):
        table_class = self.__class__
        if not self.number:
            q = db.query(table_class)
            max = (q
                   .exclude(id=q.arg(self.id).coalesce(0))
                   .fetch_max('number'))
            self.number = max and max + 1 or 1
        else:
            look_up = db.get(table_class, number=self.number)
            if look_up != self:
                raise ValueError(f'Catalog number <{self.number}> is not unique')

    def _before_insert(self, db: DBFactory):
        self.check_number(db)

    def _before_update(self, db: DBFactory):
        self.check_number(db)

from pantra.models import expose_database
db = expose_database('system')
db.bind_module()
