from __future__ import annotations

import typing
from functools import lru_cache, wraps
import traceback
import logging
from pathlib import Path

import sass
from .common import ADict
from .settings import config

if typing.TYPE_CHECKING:
    from types import CodeType
    from .components.context import Context, HTMLTemplate

code_base: typing.Dict[str, CodeType] = {}
logger = logging.getLogger("pantra.system")

@lru_cache(None, False)
def common_globals():
    globals = {}
    exec('from pantra.imports import *', globals)
    return globals


class ContextInitFailed(Exception):
    pass


def exec_includes(lst: str, rel_name: Path, ctx_locals: typing.Dict[str, typing.Any]):
    path = rel_name.parent
    for name in lst.split(' '):
        if not name.strip(): continue
        filename = (path / name).with_suffix('.py')
        if str(filename) not in code_base:
            source = filename.read_text()
            code_base[str(filename)] = compile(source, filename, 'exec')
        exec(code_base[str(filename)], ctx_locals)


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
    common_locals = {'ctx': ctx, 'refs': ctx.refs, 'session': ctx.session, '_': ctx.session.gettext, 'logger': logger}
    ctx.locals.update(common_locals)
    if 'use' in template.attributes:
        exec_includes(template.attributes.use.strip('" \''), template.filename, ctx.locals)
    if template.text is not None:
        if not template.code:
            template.code = compile(template.text, template.filename, 'exec')
        # exec(template.code, common_globals(), self.ctx.locals)
        exec(template.code, ctx.locals)#, {'__name__': template.name})

    ctx.locals.update(initial_locals)
    if 'init' in ctx.locals:
        if ctx.locals.init() is False:
            raise ContextInitFailed()
    if 'on_restart' in ctx.locals:
        ctx.locals.on_restart()
    if 'ns_type' in ctx.locals:
        ctx.ns_type = ctx.locals.ns_type


@trace_exec
def exec_restart(ctx: Context):
    ctx.locals.on_restart()


def compile_style(ctx: Context, template: HTMLTemplate) -> str:
    if template.code:
        return template.code
    try:
        css = sass.compile(string=template.text, output_style='compressed', include_paths=[str(config.CSS_PATH)])
    except Exception as e:
        css = ''
        ctx.session.error(f'{template.filename}.scss> {e}')
    template.code = css
    return css


class ReuseException(Exception):
    pass
