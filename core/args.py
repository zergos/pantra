from __future__ import annotations

import sys
import os
import typing
from functools import wraps
from inspect import signature, _empty
import traceback
if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['ExposeToArgs', 'context_args']


def context_args(*ctx):
    def processor(f):
        @wraps(f)
        def func(self, *args, **kwargs):
            args = list(args)
            for c in ctx:
                if not args: break
                setattr(self, c, args.pop(0))
            for k, v in list(kwargs.items()):
                if k in ctx:
                    setattr(self, k, v)
                    del kwargs[k]
            for c in ctx:
                if not hasattr(self, c):
                    raise NameError
            f(self, *args, **kwargs)
        func.ctx = ctx
        return func
    return processor


class StringLocals(dict):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            return item


class ExposeToArgs(dict):
    @staticmethod
    def _split_doc(s: str) -> Tuple[List[str], Dict[str, str]]:
        info = []
        params = {}
        for l in s.splitlines():
            l = l.strip()
            if l.startswith(':param'):
                chunks = l[7:].split(':')
                params[chunks[0].strip()] = chunks[1].strip()
            else:
                if l:
                    info.append(l.strip())
        return info, params

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        cls = instance.__class__
        self.doc, self.params = ExposeToArgs._split_doc(cls.__doc__) if cls.__doc__ else ([], {})
        for attr_name in cls.__dict__:
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if not callable(attr) or attr.__doc__ is None:
                continue
            sign = []
            params = {}
            if hasattr(attr, 'ctx'):
                for name in attr.ctx:
                    sign.append(name)
                    val = ""
                    if name in cls.__annotations__:
                        t = cls.__annotations__[name]
                        type_name = t if type(t) == str else t.__name__
                        val += f'{type_name} : '
                    if name in self.params:
                        val += self.params[name]
                    if hasattr(cls, name):
                        val += f' ({getattr(cls, name)!r})'
                    params[name] = val

            info, func_params = self._split_doc(attr.__doc__)
            params.update(func_params)
            for i, (p, a) in enumerate(signature(attr).parameters.items()):
                if not i: continue
                t = a.annotation
                type_name = t if type(t) == str else t.__name__
                if p in params:
                    params[p] = f'{type_name} : {params[p]}'
                else:
                    params[p] = type_name
                if a.default is None:
                    params[p] += ' (optional)'
                elif a.default != _empty:
                    params[p] += f' ({repr(a.default)})'
                sign.append(p)
            attr.doc = info
            attr.params = params
            attr.args = ', '.join(sign)
            self[attr_name] = attr

    @staticmethod
    def _print_help(self, path=''):
        if isinstance(self, ExposeToArgs):
            label = 'Commands:'
            data = self
            sepa = '- '
            args = ('.command' if path != 'command' else '') + ' [?]'
        else:
            label= 'Parameters:'
            data = self.params
            sepa = ': '
            args = ' ' + self.args
        print(f'Usage: {os.path.basename(sys.argv[0])} {path}{args}\n')
        if self.doc:
            print('  ' + '\n  '.join(self.doc) + '\n')
        if not data:
            return
        print(label)
        max_len = max(len(k) for k in data.keys()) + 3
        for c, v in data.items():
            if isinstance(v, ExposeToArgs):
                c = f'[{c}]'
            print('  ' + c + ' ' * (max_len-len(c)) + sepa + (v if type(v) == str else ' '.join(v.doc)))

    def help(self):
        ExposeToArgs._print_help(self, 'command')

    @staticmethod
    def _execute(self, instance, path: str, commands: List[str], args: str):
        if len(commands) > 0:
            command = commands.pop(0)
            if not isinstance(self, ExposeToArgs) or command not in self:
                ExposeToArgs._print_help(self, path or 'command')
                return
            else:
                ExposeToArgs._execute(self[command], self.instance, (path+'.' if path else '')+command, commands, args)
        else:
            if args == '?':
                ExposeToArgs._print_help(self, path)
                return
            try:
                code = f'_func(_instance{", "+args if args else ""})'
                eval(code, {}, StringLocals({'_func': self, '_instance': instance}))
            except SyntaxError as e:
                print(f'{e.args[0]}\n{e.args[1][3]}\n{" " * e.args[1][2]}^')
                ExposeToArgs._print_help(self, path)
            except (TypeError, NameError):
                ExposeToArgs._print_help(self, path)
            except:
                traceback.print_exc(-1)

    def execute(self):
        if len(sys.argv) == 1:
            self.help()
            return
        expr = ' '.join(a if ' ' not in a else f'"{a}"' for a in sys.argv[1:])
        if ' ' in expr:
            right = expr.index(' ')
            args = expr[right+1:]
        else:
            right = len(expr)
            args = ''
        commands = expr[:right].split('.')
        ExposeToArgs._execute(self, self.instance, '', commands, args)
