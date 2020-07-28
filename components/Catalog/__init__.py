from __future__ import annotations

from core.components.loader import collect_template
from pony.orm import db_session
from core.models.types import EntityMeta
from components.Layout import *
from core.ctx import *

__all__ = ['render_catalog_list', 'render_catalog_form', 'render_catalog_select']


def render_catalog_list(session: Session, name: str, db: str = 'db') -> Context:
    parent, new = add_window(session, f'{name}List', session.gettext(name, many=True))
    if not new:
        return parent
    locals = {'name': name, 'db': db}
    list_form = collect_template(session, f'{name}List')
    if list_form:
        return parent.render(list_form, locals=locals)
    else:
        return parent.render('CatalogList', locals=locals)


def render_catalog_select(session: Session, name: str, callback: Callable[[Any], None], db: str = 'db') -> Context:
    _ = session.gettext
    parent, new = session['taskbar'].add_window(f'{name}Select', _('Select: {session.gettext(name)}'))
    if not new:
        return parent
    locals = {'name': name, 'db': db, 'callback': callback}
    select_form = collect_template(session, f'{name}Select')
    if select_form:
        return parent.render(select_form, locals=locals)
    else:
        return parent.render('CatalogSelect', locals=locals)


def render_catalog_form(session: Session, caller: Context, entity: EntityMeta) -> Context:
    if hasattr(entity, '_entity_'):
        name = entity._entity_.__name__
        code = entity._obj_pk_
        with db_session:
            title = str(entity._get_object())
    else:
        name = entity.__name__
        code = ''
        title = ''
    _ = session.gettext
    parent, new = session['taskbar'].add_window(f'{name}#{code}', _('New: {_(name)}') if not code else f'{_(name)}: {title}', caller)
    if not new:
        return parent
    locals = {'entity': entity}
    form = collect_template(parent.session, f'{name}Form')
    if form:
        return parent.render(form, locals=locals)
    else:
        return parent.render('EntityForm', locals=locals)
