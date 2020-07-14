from __future__ import annotations

from core.components.loader import collect_template
from core.models.types import EntityMeta
from core.ctx import *

__all__ = ['render_catalog_list', 'render_catalog_form']


def render_catalog_list(parent: AnyNode, name: str, db: str = 'db') -> Context:
    list_form = collect_template(parent.session, f'{name}List')
    if list_form:
        return parent.render(list_form)
    else:
        return parent.render('CatalogList', locals={'name': name, 'db': db})


def render_catalog_select(parent: AnyNode, name: str, db: str = 'db') -> Context:
    select_form = collect_template(parent.session, f'{name}Select')
    if select_form:
        return parent.render(select_form)
    else:
        return parent.render('CatalogList', locals={'name': name, 'db': db})


def render_catalog_form(parent: AnyNode, name: str, entity: EntityMeta) -> Context:
    form = collect_template(parent.session, f'{name}Form')
    if form:
        return parent.render(form, locals={'entity': entity})
    else:
        return parent.render('EntityForm', locals={'entity': entity})
