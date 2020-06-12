from __future__ import annotations

import os
import typing
from functools import lru_cache, wraps
import traceback

import sass
from core.common import ADict
from core.defaults import CSS_PATH

if typing.TYPE_CHECKING:
    from types import CodeType
    from components.context import Context, HTMLTemplate

code_base: typing.Dict[str, CodeType] = {}


@lru_cache(None, False)
def common_globals():
    globals = {}
    exec('from core.imports import *', globals)
    return globals


class ContextInitFailed(Exception):
    pass


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


def trace_exec(func):
    @wraps(func)
    def try_exec(ctx: Context, template: HTMLTemplate):
        try:
            func(ctx, template)
        except ContextInitFailed:
            raise
        except (ImportError, OSError) as e:
            ctx.session.error(f'{template.filename}:\n{e}')
        except Exception as e:
            if len(e.args) >= 2 and len(e.args[1]) >= 4:
                ctx.session.error(
                    f'{template.filename}:\n[{e.args[1][1]}:{e.args[1][2]}] {e.args[0]}\n{e.args[1][3]}{" " * e.args[1][2]}^')
            else:
                ctx.session.error(f'{template.filename}:\nUnexpected error: {traceback.format_exc()}')
    return try_exec


@trace_exec
def compile_context_code(ctx: Context, template: HTMLTemplate):
    initial_locals = ADict(ctx.locals) - ['init', 'on_restart']
    ctx.locals.update({'ctx': ctx, 'refs': ctx.refs, 'session': ctx.session})
    if 'namespace' in template.attributes:
        exec_includes(template.attributes.namespace.strip('" '''), template.filename, ctx.locals)
    if template.text is not None:
        if not template.code:
            template.code = compile(template.text, template.filename, 'exec')
        # exec(template.code, common_globals(), self.ctx.locals)
        exec(template.code, ctx.locals)
    ctx.locals.update(initial_locals)
    if 'init' in ctx.locals:
        if ctx.locals.init() == False:
            raise ContextInitFailed()
    if 'on_restart' in ctx.locals:
        ctx.locals.on_restart()
    if 'ns_type' in ctx.locals:
        ctx.ns_type = ctx.locals.ns_type


@trace_exec
def exec_restart(ctx: Context, template: HTMLTemplate):
    ctx.locals.on_restart()


def compile_style(ctx: Context, template: HTMLTemplate) -> str:
    if template.code:
        return template.code
    try:
        css = sass.compile(string=template.text, output_style='compressed', include_paths=[CSS_PATH])
    except Exception as e:
        css = ''
        ctx.session.error(f'{template.filename}.scss> {e}')
    template.code = css
    return css
