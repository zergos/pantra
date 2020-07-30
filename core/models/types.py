import typing
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from pony.orm import LongStr, Json
from pony.orm.core import EntityMeta, Entity, EntityProxy
from .choicefield import Choice
AnyEntity = typing.Union[EntityMeta, Entity, EntityProxy]
