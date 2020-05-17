from __future__ import annotations

import os
import typing
from functools import lru_cache

if typing.TYPE_CHECKING:
    from types import CodeType
    from components.context import Context
    from components.htmlnode import HTMLTemplate

code_base: typing.Dict[str, CodeType] = {}


@lru_cache(None, False)
def common_globals():
    globals = {}
    exec('from core.imports import *', globals)
    return globals


def exec_includes(lst: str, rel_name: str, ctx_locals: typing.Dict[str, typing.Any]):
    path = os.path.dirname(rel_name)
    for name in lst.split(' '):
        if not name.strip(): continue
        filename = os.path.join(path, name) + '.py'
        if filename not in code_base:
            with open(filename, 'rt') as f:
                source = f.read()
            code_base[filename] = compile(source, filename, 'exec')
        exec(code_base[filename], ctx_locals)


def compile_context_code(ctx: Context, template: HTMLTemplate):
    initial_locals = dict(ctx.locals)
    ctx.locals.update({'ctx': ctx, 'refs': ctx.refs})
    try:
        if 'namespace' in template.attributes:
            exec_includes(template.attributes.namespace.strip('" '''), template.filename, ctx.locals)
        if not template.code:
            template.code = compile(template.text, template.filename, 'exec')
        # exec(template.code, common_globals(), self.ctx.locals)
        exec(template.code, ctx.locals)
        ctx.locals.update(initial_locals)
        if 'init' in ctx.locals:
            ctx.locals.init()
        if 'ns_type' in ctx.locals:
            ctx.ns_type = ctx.locals.ns_type
    except (ImportError, OSError) as e:
        ctx.session.error_later(f'{template.filename}:\n{e}')
    except Exception as e:
        if len(e.args) >= 2 and len(e.args[1]) >= 4:
            ctx.session.error_later(
                f'{template.filename}:\n[{e.args[1][1]}:{e.args[1][2]}] {e.args[0]}\n{e.args[1][3]}{" " * e.args[1][2]}^')
        else:
            ctx.session.error_later(f'{template.filename}:\n{e}')
