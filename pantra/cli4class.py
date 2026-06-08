"""`cli4class` provides CLI access to class members directly

Main entry point: :func:`run_command`.

Example::

    from cli4class import run_command

    class Main:
        \"\"\"one class is always `main`\"\"\"
        def job(self, a: int, b: str, c: bool, d: bool = False):
            \"\"\"do some job

            Args:
                a: integer argument
                b: string argument
                c: boolean argument
                d: boolean argument with default value
            \"\"\"

    class Group:
        \"\"\"do something different\"\"\"
        def job2(self, something: str):
            \"\"\"do another job

            Args:
                something: simple argument
            \"\"\"

    run_command(Main, ["?"])
    run_command(Main, ["job", "?"])
    run_command(Main, ["job", "1", "a", "t", "--d"])

    joined = {
        "main": Main,
        "group": Group,
    }
    run_command(joined, ["?"])
    run_command(joined, ["job", "?"])
    run_command(joined, ["group", "?"])
    run_command(joined, ["group.job2", "?"])
    run_command(joined, ["group.job2", "abc"])

Notes:

    * to print usage information use command with argument: "?", "-h" or "--help"
    * groups, subgroups and methods names separated by dot (.): group.subgroup.command
    * each optional argument could be specified in five forms:

     * by positional value
     * by assignment expression (arg=value)
     * by assignment as flag (-arg=value)
     * by assignment as GNU flag (-\\-arg=value)
     * value can be omitted for optional boolean args (--arg)

    * `t` = True, `f` = False
    * each value is being parsed as Python constant (using :func:`ast.literal_eval`), otherwise, treated as string
    * all default values specified as lambdas will be evaluated
"""
from __future__ import annotations

import inspect
import sys
import typing
import types
from functools import wraps
from pathlib import Path
from textwrap import indent
import re
import ast

if sys.version_info >= (3, 14):
    import annotationlib

from docstring_parser import parse, Docstring

__all__ = ['extra_args', 'allowed', 'run_command']

MAIN_CLASS_NAME = "main"

OptsType = dict[str, typing.Union[type, 'OptsType']]
MethodType = typing.Callable[[...], None]

class CommandException(Exception):
    pass

def extra_args(*x_args):
    """Decorator for class method to add common arguments list.

    Arguments should be declared and annotated as class attributes.

    Example::

        class Main:
            \"\"\"Group description

            Args:
                foo: common argument
            \"\"\"
            foo: str = "bar"

            @extra_args("foo")
            def job(self, other: str):
                \"\"\"simple job here

                Args:
                    other: local argument
                \"\"\"
                print(self.foo, other)

    Note:
        Extra args are inserting in the beginning and before all other defined args of the method.
        To keep default value use "-" symbol::

            run_command(Main, ["job", "-", "bar"])

    It also works with inherited classes::

        class FooProvider:
            \"\"\"Provides `foo` attr

            Args:
                foo: common argument
            \"\"\"
            foo: str = "bar"

        class Main:
            \"\"\"Group description\"\"\"
            @extra_args("foo")
            def job(self, other: str):
                ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self: CommandSpec, *args, **kwargs):
            src_args = list(args)
            # process extra args
            for arg_name in x_args:
                default_value = getattr(self.__class__, arg_name, None)
                if callable(default_value):
                    default_value = default_value()
                if src_args:
                    value = src_args.pop(0)
                    if value == "-":
                        value = default_value
                else:
                    value = default_value
                if value is None:
                    raise CommandException(f'Argument `{arg_name}` is not detected or specified')
                setattr(self, arg_name, value)
            # evaluate lambdas
            for idx in range(len(src_args)):
                if callable(src_args[idx]):
                    src_args[idx] = src_args[idx]()
            for arg_name, arg_value in list(kwargs.items()):
                if callable(arg_value):
                    kwargs[arg_name] = arg_value()
            # chain call
            func(self, *src_args, **kwargs)
        wrapper.extra_args = x_args
        if hasattr(func, "allowed"):
            wrapper.allowed = True
        return wrapper
    return decorator

def allowed(func):
    """Decorator to make method allowed to run from CLI.

    All methods are allowed by default. However, it is possible to forbid access by meta flag:
    `:meta restricted:` - it should be specified in class description. Then method should be explicitly allowed.

    Example::

        class Main:
            \"\"\"Group description

            :meta restricted:
            \"\"\"
            @allowed
            def job(self):
                \"\"\"it is callable explicitly\"\"\"
    """
    func.allowed = True
    return func

class CommandSpec:
    def __init__(self, opts:OptsType, args, silent: bool = False):
        self.opts: OptsType = opts
        self.args: list[str] | None = args
        self.command: str = MAIN_CLASS_NAME if not args else self.args.pop(0)
        self.cls, self.method = self.get_class_method()
        self.silent: bool = silent

    def get_class_method(self) -> tuple[type | None, MethodType | None]:
        cls = self.opts.get(MAIN_CLASS_NAME, None)
        member = None
        for name in self.command.split('.'):
            if member is not None:
                raise CommandException(f'Command "{self.command}" syntax error')

            if name not in self.opts:
                if hasattr(cls, name):
                    member = getattr(cls, name)
                else:
                    raise CommandException(f'Command `{name}` is not defined')
            elif isinstance((cls:=self.opts[name]), dict):
                self.opts = cls
                cls = self.opts.get(MAIN_CLASS_NAME, None)
            elif name != MAIN_CLASS_NAME:
                self.opts = {}

        return cls, member

    @staticmethod
    def get_annotations(cls: type | MethodType) -> dict[str, type | str]:
        if sys.version_info < (3, 14):
            if inspect.isclass(cls):
                annotations = {}
                for base in reversed(cls.__mro__):
                    annotations.update(getattr(base, '__annotations__', {}))
            else:
                annotations = getattr(cls, '__annotations__', {})
        else:
            annotations = annotationlib.get_annotations(cls, format=annotationlib.Format.STRING)
        return annotations

    def get_docs(self, obj: type | MethodType) -> Docstring:
        docs = parse(obj.__doc__)
        if inspect.isclass(obj):
            for inherited_cls in obj.__mro__[1:-1]:
                sub_docs = parse(inherited_cls.__doc__)
                docs.meta.extend(sub_docs.meta)
        annotations = self.get_annotations(obj)
        for param in docs.params:
            if param.type_name is None and param.arg_name in annotations:
                param.type_name = annotations[param.arg_name]
        if isinstance(obj, types.FunctionType):
            if hasattr(obj, "extra_args"):
                cls_docs = self.get_docs(self.cls)
                extra_params = []
                for arg_name in obj.extra_args:
                    param = next((param for param in cls_docs.params if param.arg_name == arg_name), None)
                    if param is None:
                        raise CommandException(f"No such common attribute `{arg_name}` annotated in class `{self.cls}`")
                    extra_params.append(param)
                docs.meta[0:0] = extra_params
            defaults = obj.__wrapped__.__defaults__ if hasattr(obj, "__wrapped__") else obj.__defaults__
            if defaults:
                for i in range(len(defaults)):
                    idx = len(docs.params) - len(defaults) + i
                    docs.params[idx].default = defaults[i]
                    docs.params[idx].is_optional = True
        else:
            for param in docs.params:
                if hasattr(obj, param.arg_name):
                    default = getattr(obj, param.arg_name)
                    if callable(default):
                        default = default()
                    if default is not None:
                        param.default = default
        return docs

    def get_commands(self, cls: type) -> list[tuple[str, MethodType, Docstring]]:
        res = []
        allow_all = ':meta restricted:' not in cls.__doc__
        for name, member in cls.__dict__.items():
            if (not name.startswith('_')
                    and isinstance(member, types.FunctionType)
                    and member.__doc__ is not None
                    and allow_all or hasattr(member, "_allowed")):
                res.append((name, member, self.get_docs(member)))
        return res

    def print_usage(self):
        if self.silent:
            return
        if self.method is None:
            print(f'\nUsage: {Path(sys.argv[0]).name} {self.command+"." if self.command!=MAIN_CLASS_NAME else "[group]."}<command> [?]\n')
            print(indent(self.get_docs(self.cls).description.strip(), '  '))
            commands = self.get_commands(self.cls)
            if not commands:
                return
            print('\nCommands:\n')
            max_len = max(len(name[0]) for name in commands) + 1
            for name, member, doc in commands:
                print(f'  {name}' + ' '*(max_len-len(name)) + '- ' + doc.short_description)
            if len(self.opts)>1:
                print('\nGroups:\n')
                max_len = max(len(name) for name in self.opts) + 1
                for group_name, group_value in self.opts.items():
                    if group_name == MAIN_CLASS_NAME:
                        continue
                    print(f'  {group_name}' + ' '*(max_len-len(group_name)) + '- ', end="")
                    if isinstance(group_value, dict):
                        doc = self.get_docs(group_value.get(MAIN_CLASS_NAME))
                    else:
                        doc = self.get_docs(group_value)
                    print(doc.short_description.strip())
        else:
            docs = self.get_docs(self.method)
            args = [f'[{param.arg_name}]' if param.is_optional else f'<{param.arg_name}>' for param in docs.params]
            print(f'\nUsage: {Path(sys.argv[0]).name} {self.command} [?] ' + ' '.join(args) + '\n')
            print(indent(docs.description.strip(), '  '))
            if not docs.params:
                return
            print('\nArguments (name: type - description = default):\n')
            max_len = max(len(param.arg_name) for param in docs.params) + 1
            type_len = max(len(param.type_name) for param in docs.params) + 1
            for param in docs.params:
                print(f'  {param.arg_name}' + ' '*(max_len-len(param.arg_name)), end="")
                if param.type_name is not None:
                    print(': ' + param.type_name + ' '*(type_len-len(param.type_name)), end="")
                print('- ' + param.description, end="")
                if param.default is not None:
                    default = param.default() if callable(param.default) else param.default
                    print(f' = {default!r}')
                else:
                    print()

    def process_command(self):
        try:
            if self.method is None or self.args and self.args[0] in ('?', '-h', '--help'):
                raise CommandException

            docs = self.get_docs(self.method)
            required_args_count = sum(1 for param in docs.params if not param.is_optional)
            if hasattr(self.method, 'extra_args') and len(self.method.extra_args) == required_args_count: # noqa
                required_args_count = 0

            def get_value(v: str) -> int | bool | str | dict:
                if v == 'y':
                    return True
                if v == 'n':
                    return False
                try:
                    return ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    return v

            re_assign = re.compile(r'-{0,2}(\w(\w|\d|_)+)=(.+)')
            f_args = []
            f_kwargs = {}
            param_names = [param.arg_name for param in docs.params]

            for arg in self.args:
                expr = re.search(re_assign, arg)
                if not expr:
                    if len(arg)>1 and arg.startswith('-'):
                        arg = arg.lstrip('-')
                        if arg not in param_names:
                            raise CommandException(f'Unknown boolean argument: `{arg}`')
                        f_kwargs[arg] = True
                    else:
                        f_args.append(get_value(arg))
                else:
                    arg_name = expr.group(1)
                    if arg_name not in param_names:
                        raise CommandException(f'Unknown argument: `{arg_name}`')
                    f_kwargs[arg_name] = get_value(expr.group(3))

            if len(f_args) < required_args_count:
                raise CommandException(f"Required argument `{docs.params[len(f_args)-1].arg_name}` not specified.")

            if len(f_args) + len(f_kwargs) > len(param_names):
                raise CommandException("Too many arguments specified.")

            try:
                if not self.silent:
                    print(f"\nRunning command `{self.command}()`:")
                self.method(self.cls(), *f_args, **f_kwargs)
            except SyntaxError as e:
                raise CommandException(f'{e.args[0]}\n{e.args[1][3]}\n{" " * e.args[1][2]}^')

        except CommandException as e:
            print(e)
            self.print_usage()

def run_command(opts: typing.Union[type, OptsType], args: list[str] | None, silent: bool = False):
    """Main CLI entrypoint.

    Args:
        opts: specify class or tree structure with several classes
        args: list of arguments as it comes from `sys.argv`
        silent: whether to suppress printing of usage info

    Note:

        In tree structure "main" group should be defined, but omitted at command prompt.
        It could be several levels deep::

            {
                "main": Main,
                "group": {
                    "main": Group,
                    "subgroup": {
                        "main": SubGroup,
                        "subsubgroup": SubSubGroup,
                    }
                }
            }

        The path to the deepest command will be following::

            run_command(..., ['group.subsubgroup.subsubgroup.command', ...])
    """
    if inspect.isclass(opts):
        opts = {MAIN_CLASS_NAME: opts}
    if MAIN_CLASS_NAME not in opts:
        raise ValueError(f'No `{MAIN_CLASS_NAME}` command class in `opts`')
    if args is None:
        args = sys.argv[1:]
    cmd = CommandSpec(opts, args, silent)
    cmd.process_command()
