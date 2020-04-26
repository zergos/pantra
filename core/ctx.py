from typing import *
from dataclasses import *

from attrdict import AttrDict
from core.components.controllers import *
from core.components.context import *

if 'ctx' not in globals():
    refs = AttrDict()
    ctx = AttrDict()
