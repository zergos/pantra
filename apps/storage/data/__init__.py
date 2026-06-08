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

    class Row(Document.Row):
        good: Good
        unit: Unit
        qty: float


from pantra.models import expose_database
db = expose_database('storage')
db._debug_mode = True
db.bind_module()
