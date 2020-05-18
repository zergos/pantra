from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core.common import ADict
    from core.components.context import Context
    from session import Session
    from typing import *

    refs: ADict
    ctx: Context
    session: Session
