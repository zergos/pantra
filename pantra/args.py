from __future__ import annotations

import sys
from pathlib import Path
import types
import typing
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from inspect import signature, _empty
import traceback
import re
import json
if typing.TYPE_CHECKING:
    from typing import *

__all__ = ['ExposeToArgs', 'context_args', 'Empty']


def context_args(*ctx_args):
    def processor(f):
        @wraps(f)
        def func(self, *args, **kwargs):
            empty_ctx = list(arg_name for arg_name in ctx_args if
                             arg_name not in func.flags
                             #and getattr(self, arg_name, Empty) is Empty
                             and arg_name not in kwargs)
            for k, v in zip(empty_ctx, args):
                if v != '-':
                    setattr(self, k, v)
            args = list(args)[min(len(empty_ctx), len(args)):]
            for k, v in list(kwargs.items()):
                if k in ctx_args:
                    setattr(self, k, v)
                    del kwargs[k]
            for arg_name in ctx_args:
                if getattr(self, arg_name, Empty) is Empty:
                    raise ArgsError(f"argument `{arg_name}` not specified")
            f(self, *args, **kwargs)
        func.ctx = ctx_args
        func.flags = ()
        return func
    return processor


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

        new_args.extend(args)

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


class ExposeToArgs(dict):
    cls: type
    doc: str
    params: dict[str, ArgParam]

    @staticmethod
    def _split_doc(s: str) -> tuple[list[str], dict[str, ArgParam]]:
        info = []
        params = {}
        for l in s.splitlines():
            l = l.strip()
            if l.startswith(':param'):
                chunks = l[7:].split(':')
                params[chunks[0].strip()] = ArgParam(':'.join(chunks[1:]).strip())
            elif l:
                info.append(l.strip())
        return info, params

    def __init__(self, cls: type):
        super().__init__()
        self.cls = cls
        self.doc, self.params = ExposeToArgs._split_doc(cls.__doc__) if cls.__doc__ else ([], {})
        for method_name in list(cls.__dict__):
            if method_name.startswith('_'):
                continue
            method = getattr(cls, method_name)
            if not callable(method) or method.__doc__ is None:
                continue
            params: dict[str, ArgParam] = defaultdict(ArgParam)
            flags = []
            # has context args?
            if hasattr(method, 'ctx'):
                for name in method.ctx:
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

            info, func_params = self._split_doc(method.__doc__)
            params.update(func_params)
            for i, (p, a) in enumerate(signature(method).parameters.items()):
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

            method.doc = info
            method.params = params
            method.args = args
            method.flags = flags
            self[method_name] = method

    def add_commands(self, cls):
        self[cls.__name__.lower()] = ExposeToArgs(cls)

    @staticmethod
    def _print_help(function, path=''):
        if isinstance(function, ExposeToArgs):
            label = 'Commands:'
            data = function
            args = ('.command' if path != 'command' else '') + ' [?]'
            type_len = 1
        else:
            label= 'Parameters:'
            data = function.params
            args = ' ' + ', '.join('?'+arg if data[arg].default else arg for arg in function.args)
            type_len = max(len(t) for v in data.values() for t in [v.type]) + 1 if data else 0
        print(f'Usage: {Path(sys.argv[0]).name} {path}{args}\n')
        if function.doc:
            print('  ' + '\n  '.join(function.doc) + '\n')
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
    def _execute(function, cls: type, path: str, commands: list[str], args: list[str]):
        if len(commands) > 0:
            command = commands.pop(0)
            if not isinstance(function, ExposeToArgs) or command not in function:
                ExposeToArgs._print_help(function, path or 'command')
                return
            else:
                ExposeToArgs._execute(function[command], function.cls, (path + '.' if path else '') + command, commands, args)
        else:
            if not callable(function) or args and args[0] == '?':
                ExposeToArgs._print_help(function, path)
                return
            re_assign = re.compile(r'((\w|\d|_)+)=(.+)')
            re_number = re.compile(r'^\d+$')
            re_dict = re.compile(r'^\{\}$')
            f_args = []
            f_kwargs = {}
            def get_value(v: str) -> int | bool | str | dict:
                if v == 'y':
                    return True
                if v == 'n':
                    return False
                if re.match(re_number, v):
                    return int(v)
                if re.match(re_dict, v):
                    return json.loads(v)
                return v

            for arg in args:
                check = re.search(re_assign, arg)
                if not check:
                    if arg.startswith('--') and arg[2:] in function.flags:
                        f_kwargs[arg[2:]] = True
                    else:
                        f_args.append(get_value(arg))
                else:
                    f_kwargs[check.group(1)] = get_value(check.group(3))
            try:
                function(cls(), *f_args, **f_kwargs)
            except SyntaxError as e:
                print(f'{e.args[0]}\n{e.args[1][3]}\n{" " * e.args[1][2]}^')
                ExposeToArgs._print_help(function, path)
            except ArgsError as e:
                print(str(e))
                ExposeToArgs._print_help(function, path)
            except:
                traceback.print_exc(-1)
                raise

    def execute(self, argv=None):
        if argv is None:
            argv = sys.argv
        if len(argv) <= 1:
            self.help()
            return
        ExposeToArgs._execute(self, self.cls, '', argv[1].split('.'), argv[2:])
