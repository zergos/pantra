from __future__ import annotations
from pantra.ctx import *

__all__ = ['make_dialog']


def make_dialog(ctx: Context, text: str, buttons: str = None, callback: Callable[[str], None] = None):
    c = ctx.render('Dialog', locals={'text': text}, build=False)
    if buttons:
        c['buttons'] = buttons
    if callback:
        c['callback'] = callback
    c.renderer.build()
    return c

