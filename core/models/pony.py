from __future__ import annotations

import typing
from collections import defaultdict

from core.defaults import *
from .parser import parse_xml
from .runtime import EVENTS

if typing.TYPE_CHECKING:
    from typing import *

pony_types = ('bool', 'int', 'float', 'str', 'bytes', 'Decimal', 'datetime', 'date', 'time', 'timedelta', 'UUID', 'LongStr', 'Json')


def _pony_collect_models(app: str) -> Tuple[Dict, Dict, str]:
    # parse referred models
    file_name = os.path.join(APPS_PATH, app, 'data', 'databases.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    python = ''

    models: Dict[str, List[str]] = {}  # entity name / lines
    set_later: Dict[str, List[str]] = defaultdict(list)  # entity name / attr

    def start_element(name: str, attrs: dict):
        nonlocal python, models, set_later
        if name == 'reuse' and attrs['name'] == 'db':
            _models, _set_later, _python = _pony_collect_models(attrs['app'])
            models.update(_models)
            set_later.update(_set_later)
            python += _python

    parse_xml(file_name, start_element)

    # parse current models
    file_name = os.path.join(APPS_PATH, app, 'data', 'models.xml')
    if not os.path.exists(file_name):
        raise FileExistsError(file_name)

    in_python = False

    entity_name = ''
    lines = []

    def start_element(name: str, attrs: dict):
        nonlocal in_python, set_later, entity_name, lines

        if name == 'entity':
            lines = []
            entity_name = attrs['name']
            models[entity_name] = lines
            lines.append('\n    class {}({}{}):'.format(entity_name, attrs.get('base', 'EntityMeta'), ', '+attrs['mixin'] if 'mixin' in attrs else ''))
            if 'display' in attrs:
                lines.append(f'    def __str__(self):\n            return {attrs["display"]}')
            for event in EVENTS:
                if event in attrs:
                    lines.append(f'    {event} = {attrs[event]}')
            lines.append('')
        elif name in ('attr', 'array', 'prop'):
            attr_name = attrs['name']
            if 'choices' in attrs:
                field = 'Choice'
            elif attrs.get('cid', 'False') != 'False':
                field = 'Discriminator'
            else:
                field = 'Optional' if attrs.get('required', 'False') == 'False' else 'Required'
            t = ''
            pars = []
            for a, v in attrs.items():
                if a == 'type':
                    t = v
                    if name == 'attr':
                        pars.append(t)
                        if t not in pony_types:
                            if 'reverse' not in attrs:
                                reverse_name = f'{entity_name.lower()}s'
                                pars.append(f"reverse='{reverse_name}'")
                            else:
                                reverse_name = attrs['reverse']
                            set_later[t].append((reverse_name, entity_name))
                elif a == 'default':
                    if t in ('int', 'float', 'Decimal', 'Json', 'bool'):
                        pars.append(f'{a}={v}')
                    else:
                        pars.append(f"{a}='{v}'")
                elif a == 'eval':
                    pars.append(f"default='{v}'")
                elif a == 'choices':
                    pars.append(f"{a}={v}")
                elif a == 'index':
                    if attrs['index'] != 'False':
                        pars.append('index=True')
                elif a in ('precision', 'sql_default', 'unique', 'reverse'):
                    pars.append(f"{a}='{v}'")
            if name == 'attr':
                lines.append(f'    {attr_name} = {field}({", ".join(pars)})')
            elif name == 'array':
                lines.append(f'    {attr_name} = {t.capitalize()}Array({", ".join(pars)})')
            elif name == 'prop':
                lines.extend(f'''    @property
    def {attr_name}(self):
        return self.body['{attr_name}']
    @{attr_name}.setter
    def {attr_name}(self, value):
        self.body['{attr_name}'] = value'''.splitlines())
        elif name == 'set':
            attr_name = attrs['name']
            t = attrs['type']
            lines.append(f'    {attr_name} = Set("{t}")')
        elif name == 'python':
            in_python = True

    def end_element(name: str):
        nonlocal in_python
        if name == 'python':
            in_python = False
        elif name == 'entity':
            lines.append(f'''
        def __getitem__(self, item):
            return {entity_name}()
        def __iter__(self):
            yield {entity_name}()
''')

    def char_data(data):
        nonlocal python
        if in_python:
            python += data

    parse_xml(file_name, start_element, end_element, char_data)

    return models, set_later, python.strip()


def expose_to_pony(app: str, with_init: bool = True):

    models, set_later, python = _pony_collect_models(app)

    # add attrs with refs
    for model_name, attrs in set_later.items():
        for attr_name, entity_name in attrs:
            attr_text = f'    {attr_name} = Set("{entity_name}")'
            found = False
            for line in reversed(models[model_name]):
                if attr_text in line:
                    found = True
                    break
            if not found:
                models[model_name].append(attr_text)

    body: List = f'''# ---- auto-generated {app} models for type checker
from __future__ import annotations
import typing'''.splitlines()
    if with_init:
        body.append('''
from core.models import dbinfo, expose_databases

__all__ = ['db']
''')
    body.append('''
if typing.TYPE_CHECKING:
    from core.models.types import *
    from pony.orm import *
''')

    body.extend([f'    {line}' for line in python.splitlines()])
    for lines in models.values():
        body.append('')
        body.extend([f'    {line}' for line in lines])

    body.append('')
    body.append('    class DB:')
    for model_name in models.keys():
        body.append(f'        {model_name}: {model_name}')
    body.append('')

    if with_init:
        body.append(f"""if '{app}' not in dbinfo:
    expose_databases('{app}')    
db: DB = dbinfo['{app}']['db'].factory.cls
""")

    with open(os.path.join(APPS_PATH, app, 'data', '__init__.py'), 'wt') as f:
        f.write('\n'.join(body))
