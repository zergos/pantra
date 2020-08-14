from __future__ import annotations

import sys
import os
import types
import typing
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from inspect import signature, _empty
import traceback
if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['ExposeToArgs', 'context_args', 'Empty']


def context_args(*ctx):
    def processor(f):
        @wraps(f)
        def func(self, *args, **kwargs):
            for k, v in list(kwargs.items()):
                if k in ctx:
                    setattr(self, k, v)
                    del kwargs[k]
            for c in ctx:
                if not hasattr(self, c):
                    raise ArgsError(f"argument '{c}' not specified")
            f(self, *args, **kwargs)
        func.ctx = ctx
        return func
    return processor


class Flag(str):
    pass


class Empty:
    pass


class ArgsError(Exception):
    pass


def parse_args(f):
    def func(*args, **kwargs):
        args = list(args)

        # parse required args
        new_args = [args.pop(0)]
        for a in f.args:
            default = f.params[a].value
            if default is Empty:
                if args:
                    kwargs[a] = args.pop(0)
                elif a not in kwargs:
                    raise ArgsError(f'required positional argument: {a}')
            elif default is None:
                if args:
                    kwargs[a] = args.pop(0)
            elif default is not False and a not in kwargs:
                kwargs[a] = default

        # parse flags
        for a in args:
            if type(a) == Flag:
                kwargs[str(a)] = True
            else:
                new_args.append(a)

        # check unknown args
        for a in kwargs:
            if a not in f.args:
                raise ArgsError(f'arg {a} is unknown')

        f(*new_args, **kwargs)
    return func


@dataclass
class ArgParam:
    doc: str = field(default_factory=str)
    type: str = field(default_factory=str)
    default: str = field(default_factory=str)
    value: Any = field(default=Empty)


class StringLocals(dict):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            return item


class ExposeToArgs(dict):
    instance: ClassVar
    doc: str
    params: Dict[str, ArgParam]

    @staticmethod
    def _split_doc(s: str) -> Tuple[List[str], Dict[str, ArgParam]]:
        info = []
        params = {}
        for l in s.splitlines():
            l = l.strip()
            if l.startswith(':param'):
                chunks = l[7:].split(':')
                params[chunks[0].strip()] = ArgParam(chunks[1].strip())
            elif l:
                info.append(l.strip())
        return info, params

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        cls = instance.__class__
        self.doc, self.params = ExposeToArgs._split_doc(cls.__doc__) if cls.__doc__ else ([], {})
        for attr_name in list(cls.__dict__):
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if not callable(attr) or attr.__doc__ is None:
                continue
            params: Dict[str, ArgParam] = defaultdict(ArgParam)
            flags = []
            if hasattr(attr, 'ctx'):
                for name in attr.ctx:
                    if name in self.params:
                        params[name].doc = self.params[name].doc

                    type_name = ''
                    if name in cls.__annotations__:
                        t = cls.__annotations__[name]
                        type_name = t if type(t) == str else t.__name__
                        params[name].type = type_name

                    if hasattr(cls, name):
                        if type_name == 'bool':
                            params[name].value = getattr(cls, name)
                            params[name].default = 'option'
                            flags.append(name)
                        else:
                            default = getattr(cls, name)
                            if callable(default):
                                default = default()
                                setattr(cls, name, default)
                            if default == Empty:
                                delattr(cls, name)
                            else:
                                params[name].value = default
                                params[name].default = repr(default)

            info, func_params = self._split_doc(attr.__doc__)
            params.update(func_params)
            for i, (p, a) in enumerate(signature(attr).parameters.items()):
                if not i: continue  # first arg is always self
                t = a.annotation
                type_name = t if type(t) == str else t.__name__
                if p in params:
                    params[p].doc = params[p].doc
                params[p].type = type_name
                if a.default is None:
                    params[p].value = None
                    params[p].default = 'optional'
                elif a.default != _empty:
                    if type_name == 'bool':
                        params[p].value = a.default
                        params[p].default = 'option'
                        flags.append(p)
                    else:
                        params[p].value = a.default
                        params[p].default = repr(a.default)

            # sort by optional state
            args = []
            for k, a in params.items():
                if not a.default:
                    args.append(k)
            for k, a in params.items():
                if a.default:
                    args.append(k)

            attr.doc = info
            attr.params = params
            attr.args = args
            attr.flags = flags
            self[attr_name] = attr

    def add_commands(self, instance):
        self[instance.__class__.__name__.lower()] = ExposeToArgs(instance)

    @staticmethod
    def _print_help(self, path=''):
        if isinstance(self, ExposeToArgs):
            label = 'Commands:'
            data = self
            args = ('.command' if path != 'command' else '') + ' [?]'
            type_len = 1
        else:
            label= 'Parameters:'
            data = self.params
            args = ' ' + ', '.join('?'+arg if data[arg].default else arg for arg in self.args)
            type_len = max(len(t) for v in data.values() for t in [v.type]) + 1 if data else 0
        print(f'Usage: {os.path.basename(sys.argv[0])} {path}{args}\n')
        if self.doc:
            print('  ' + '\n  '.join(self.doc) + '\n')
        if not data:
            return
        print(label)
        max_len = max(len(k) for k in data) + 3
        for c, v in data.items():
            if isinstance(v, ExposeToArgs):
                c = f'[{c}]'
            line = '  ' + c + ' ' * (max_len-len(c))
            if isinstance(v, (ExposeToArgs, types.FunctionType)):
                line += f' - ' + ' '.join(v.doc)
            elif isinstance(v, ArgParam):
                if v.type:
                    line += ': ' + v.type + ' ' * (type_len-len(v.type))
                line += ': ' + v.doc
                if v.default:
                    line += f' ({v.default})'
            print(line)

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
            if not callable(self) or args == '?':
                ExposeToArgs._print_help(self, path)
                return
            try:
                code = f'{self.__name__}(_{", "+args if args else ""})'
                locals = StringLocals({self.__name__: parse_args(self), '_': instance, 'y': True, 'n': False})
                for f in self.flags:
                    locals[f] = Flag(f)
                eval(code, {}, locals)
            except SyntaxError as e:
                print(f'{e.args[0]}\n{e.args[1][3]}\n{" " * e.args[1][2]}^')
                ExposeToArgs._print_help(self, path)
            except ArgsError as e:
                print(str(e))
                ExposeToArgs._print_help(self, path)
            except:
                traceback.print_exc(-1)

    def execute(self, argv=None):
        if argv is None:
            argv = sys.argv
        if len(argv) <= 1:
            self.help()
            return
        expr = ' '.join(a if ' ' not in a else f'"{a}"' for a in argv[1:])
        if ' ' in expr:
            right = expr.index(' ')
            args = expr[right+1:]
        else:
            right = len(expr)
            args = ''
        commands = expr[:right].split('.')
        ExposeToArgs._execute(self, self.instance, '', commands, args)
