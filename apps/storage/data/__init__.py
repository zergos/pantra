from __future__ import annotations
from apps.system.data import Catalog, Document

_SCHEMA_ = "storage"


class Storage(Catalog):
    pass


class Unit(Catalog):
    pass


class Good(Catalog):
    unit: Unit
    weight: float
    

class Purchase(Document):
    storage: Storage

    class PurchaseLine(Document.DocumentLine):
        good: Good
        unit: Unit
        qty: float


from pantra.models import expose_database
db = expose_database('storage')
db.use_module()
