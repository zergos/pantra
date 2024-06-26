from __future__ import annotations
import typing

import components.Layout.grids as grids

if typing.TYPE_CHECKING:
    from pantra.components.context import Context
    from pantra.session import Session
    from typing import *

__all__ = ['add_window']


def add_window(session: Session, code: str, title: str) -> Tuple[Optional[Context], bool]:
    _ = session.gettext
    if 'taskbar' not in session:
        session.log(_('Can not add window, session has no taskbar'))
        return None, False
    return session['taskbar'].add_window(code, title)
