from typing import *
from dataclasses import *

from attrdict import AttrDict
from core.components.controllers import *
from core.components.context import *

if TYPE_CHECKING:
    refs = AttrDict()
    ctx = AttrDict()
