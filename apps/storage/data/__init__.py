# ---- auto-generated storage models for type checker
from __future__ import annotations
import typing

from pantra.models import dbinfo, expose_databases
from pony.orm import make_proxy

__all__ = ['db', 'make_proxy']


if typing.TYPE_CHECKING:
    from pantra.models.types import *
    from pony.orm import *

    import hashlib
    import uuid
    from pony.orm import *
    
    class UserMixin:
        def set_password(self, password):
            self.salt = uuid.uuid4().hex
            self.password = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()
    
        def check_password(self, password):
            check = hashlib.sha512((password + self.salt).encode('utf-8')).hexdigest()
            return check == self.password
    
    
    def catalog_auto_number(self):
        Catalog = self.__class__
        if not self.number:
            with db_session():
                amount = Catalog.select(lambda row: row.prefix == self.prefix).count()
                if not amount:
                    self.number = 1
                else:
                    max = select(o.number for o in Catalog if o.prefix == self.prefix).max()
                    self.number = max + 1
        else:
            if Catalog.get(prefix=self.prefix, number=self.number):
                raise ValueError(f'number {self.number} is not unique')

    
    class User(EntityMeta, UserMixin):
        def __str__(self):
            return {self.name}
    
        name = Required(str)
        password = Required(str)
        salt = Required(str)
        email = Optional(str)
        created_at = Required(datetime, default='datetime.now')
        is_admin = Optional(bool, default=False)
        enabled = Optional(bool, default=False)
        apps = Set("App")
    
        def __getitem__(self, item):
            return User()
        def __iter__(self):
            yield User()


    
    class App(EntityMeta):
    
        name = Required(str)
        title = Optional(str)
        users = Set("User")
    
        def __getitem__(self, item):
            return App()
        def __iter__(self):
            yield App()


    
    class Document(EntityMeta):
    
        prefix = Optional(str, default='')
        number = Optional(str)
        date = Required(datetime, default='datetime.now')
        body = Required(Json, default='dict')
    
        def __getitem__(self, item):
            return Document()
        def __iter__(self):
            yield Document()

        documentlines = Set("DocumentLine")

    
    class DocumentLine(EntityMeta):
    
        document = Required(Document, reverse='documentlines')
        pos = Required(int)
        data = Required(Json, default='dict')
    
        def __getitem__(self, item):
            return DocumentLine()
        def __iter__(self):
            yield DocumentLine()


    
    class Catalog(EntityMeta):
        def __str__(self):
            return self.name
        before_insert = catalog_auto_number
        before_update = catalog_auto_number
    
        prefix = Optional(str)
        number = Required(int)
        name = Optional(str)
        body = Required(Json, default='dict')
    
        def __getitem__(self, item):
            return Catalog()
        def __iter__(self):
            yield Catalog()


    
    class Storage(Catalog):
    
    
        def __getitem__(self, item):
            return Storage()
        def __iter__(self):
            yield Storage()


    
    class Unit(Catalog):
    
    
        def __getitem__(self, item):
            return Unit()
        def __iter__(self):
            yield Unit()


    
    class Good(Catalog):
    
        @property
        def unit(self):
            return self.body['unit']
        @unit.setter
        def unit(self, value):
            self.body['unit'] = value
        @property
        def weight(self):
            return self.body['weight']
        @weight.setter
        def weight(self, value):
            self.body['weight'] = value
    
        def __getitem__(self, item):
            return Good()
        def __iter__(self):
            yield Good()


    class DB:
        User: User
        App: App
        Document: Document
        DocumentLine: DocumentLine
        Catalog: Catalog
        Storage: Storage
        Unit: Unit
        Good: Good

if 'storage' not in dbinfo:
    expose_databases('storage')    
db: DB = dbinfo['storage']['db'].factory.cls
