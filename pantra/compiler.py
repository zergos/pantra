from __future__ import annotations

import typing
from functools import lru_cache, wraps
import traceback
import logging
from pathlib import Path
from dataclasses import dataclass
import ast

import sass
from .settings import config

if typing.TYPE_CHECKING:
    from typing import Self, Optional
    from types import CodeType
    from .components.context import Context, HTMLTemplate

code_base: typing.Dict[str, CodeType] = {}
logger = logging.getLogger("pantra.system")

@dataclass(slots=True)
class CodeMetrics:
    has_node_processor: bool = False
    has_init: bool = False
    has_on_restart: bool = False
    has_on_render: bool = False
    has_ns_type: bool = False

    @staticmethod
    def collect(code_string: str) -> Optional[CodeMetrics]:
        try:
            tree = ast.parse(code_string)
        except SyntaxError:
            return None

        res = CodeMetrics()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == 'node_processor':
                    res.has_node_processor = True
                elif node.name == 'init':
                    res.has_init = True
                elif node.name == 'on_restart':
                    res.has_on_restart = True
                elif node.name == 'on_render':
                    res.has_on_render = True
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if type(target) is ast.Name and target.id == 'ns_type':
                        res.has_ns_type = True
                        break
        return res

    def add(self, other: Self) -> Self:
        for key in self.__slots__:
            setattr(self, key, getattr(self, key) or getattr(other, key))
        return self

@lru_cache(None, False)
def common_globals():
    globals = {}
    exec('from pantra.imports import *', globals)
    return globals


class ContextInitFailed(Exception):
    pass


def exec_includes(lst: str, rel_name: Path, ctx_locals: typing.Dict[str, typing.Any], code_metrics: Optional[CodeMetrics]) -> CodeMetrics:
    path = rel_name.parent
    for name in lst.split(' '):
        if not name.strip(): continue
        filename = (path / name).with_suffix('.py')
        if str(filename) not in code_base:
            source = filename.read_text()
            if code_metrics is not None:
                code_metrics.add(CodeMetrics.collect(source))
            code_base[str(filename)] = compile(source, filename, 'exec')
        exec(code_base[str(filename)], ctx_locals)
    return code_metrics


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
    initial_values = {k:v for k,v in ctx.locals.items() if k not in ('init', 'on_restart', 'ctx', 'refs')}
    common_locals = {'ctx': ctx, 'refs': ctx.refs, 'session': ctx.session, '_': ctx.session.gettext, 'logger': logger}
    ctx.locals.update(common_locals)
    code_metrics: CodeMetrics = CodeMetrics() if not template.code_metrics else None
    if 'use' in template.attributes:
        exec_includes(template.attributes['use'].strip('" \''), template.filename, ctx.locals, code_metrics)
    if template.content is not None:
        if not template.code:
            template.code = compile(template.content, template.filename, 'exec')
        # exec(template.code, common_globals(), self.ctx.locals)
        exec(template.code, ctx.locals)#, {'__name__': template.name})
    if not template.code_metrics:
        template.code_metrics = code_metrics.add(CodeMetrics.collect(template.content))
    else:
        code_metrics = template.code_metrics

    ctx.locals.update(initial_values)
    if code_metrics.has_init:
        if ctx.locals.call('init') is False:
            raise ContextInitFailed()
    if code_metrics.has_on_restart:
        ctx.locals.call('on_restart')
    if code_metrics.has_ns_type:
        ctx.ns_type = ctx.locals['ns_type']


@trace_exec
def exec_restart(ctx: Context):
    ctx.locals.call('on_restart')


def compile_style(ctx: Context, template: HTMLTemplate) -> str:
    if template.code:
        return template.code
    try:
        css = sass.compile(string=template.content, output_style='compressed', include_paths=[str(config.CSS_PATH)])
    except Exception as e:
        css = ''
        ctx.session.error(f'{template.filename}.scss> {e}')
    template.code = css
    return css


class ReuseException(Exception):
    pass
