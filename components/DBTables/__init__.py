from __future__ import annotations
import inspect
from typing import Any, Callable

from quazy import DBTable

from pantra.components.loader import collect_template, HTMLTemplate
from pantra.models import dbinfo, expose_database
from pantra.session import Session
from pantra.components.context import Context

from components.Layout import *

__all__ = ['render_list', 'render_form', 'render_select']

def get_table_by_name(session: Session, table_name: str, db_name: str) -> type[DBTable]:
    db = expose_database(session.app, db_name)
    return db[table_name]


def find_template(session: Session, table: type[DBTable], suffix: str) -> HTMLTemplate | None:
    template = collect_template(session, f'{table.__qualname__}{suffix}')
    if not template:
        for base in table.__bases__:
            if issubclass(base, DBTable):
                if template:=find_template(session, base, suffix):
                    break
    return template

def find_template_by_name(session: Session, table_name: str, db_name: str, suffix: str) -> HTMLTemplate | None:
    return find_template(session, get_table_by_name(session, table_name, db_name), suffix)

def render_list(session: Session, table_name: str, db_name: str = 'db') -> Context:
    parent, new = add_window(session, f'{table_name}List', session.gettext(table_name, many=True))
    if not new:
        return parent
    list_template = find_template_by_name(session, table_name, db_name, 'List')
    locals = {'name': table_name, 'db_name': db_name}
    return parent.render(list_template, locals=locals)


def render_select(session: Session, table_name: str, callback: Callable[[Any], None], db_name: str = 'db') -> Context:
    _ = session.gettext
    parent, new = session['taskbar'].add_window(f'{table_name}Select', _('Select: {session.gettext(name)}'))
    if not new:
        return parent
    select_template = find_template_by_name(session, table_name, db_name, 'Select')
    locals = {'name': table_name, 'db_name': db_name, 'callback': callback}
    return parent.render(select_template, locals=locals)


def render_form(session: Session, caller: Context, row: DBTable | type[DBTable], values: dict[str, Any] = None) -> Context:
    if not inspect.isclass(row):
        table = row.__class__
        title = str(row)
        code = row.pk
    else:
        table = row
        title = ''
        code = ''
    _ = session.gettext
    parent, new = session['taskbar'].add_window(f'{table.__qualname__}#{code}', _('New: {_(table.__qualname__)}') if not code else f'{_(table.__qualname__)}: {title}', caller)
    if not new:
        return parent
    form_template = find_template(session, table, 'Form')
    locals = {'row': row, 'values': values or {}}
    return parent.render(form_template, locals=locals)
