from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .common import ADict
    from .components.context import Context
    from .session import Session
    from typing import *

    refs: ADict
    ctx: Context
    session: Session


def defined(name):
    return name in globals()
