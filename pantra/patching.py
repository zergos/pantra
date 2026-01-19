from __future__ import annotations

import dis, types, typing
import inspect
import ast
import textwrap

FT = typing.TypeVar('FT', bound=types.FunctionType | type)

class LoggerTransformer(ast.NodeTransformer):
    def __init__(self):
        self.has_changes = False

    def visit_Expr(self, node):
        if (isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == 'logger'):
            self.has_changes = True
            return ast.copy_location(ast.Pass(), node)
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if node.id == 'wipe_logger':
            return None
        return node

def wipe_logger(func: FT) -> FT:
    from .settings import config
    if config.ENABLE_LOGGING:
        return func

    """
    if inspect.isclass(func):
        for k, v in func.__dict__.items():
            if inspect.isfunction(v):
                setattr(func, k, wipe_logger(v))
            elif type(v) is staticmethod:
                setattr(func, k, staticmethod(wipe_logger(v.__func__)))
        return func
    """

    source_lines, line_num = inspect.getsourcelines(func)
    source = '\n' * (line_num-1) + textwrap.dedent(''.join(source_lines))
    tree = ast.parse(source)
    func_name = tree.body[0].name
    print(func_name)
    transformer = LoggerTransformer()
    new_tree = transformer.visit(tree)
    if not transformer.has_changes:
        return func
    code_obj = compile(new_tree, filename=inspect.getfile(func), mode='exec')
    if inspect.isfunction(func):
        namespace = func.__globals__.copy()
    else:
        class_func = next((k for k, v in inspect.getmembers(func) if not k.startswith('__') and inspect.isfunction(v)), None)
        namespace = getattr(func, class_func).__globals__.copy()
    exec(code_obj, namespace)
    return namespace[func_name]

"""
def wipe_logger(func: FT) -> FT:
    from .settings import config
    if config.ENABLE_LOGGING:
        return func

    if inspect.isclass(func):
        for k, v in func.__dict__.items():
            if inspect.isfunction(v):
                setattr(func, k, wipe_logger(v))
            elif type(v) is staticmethod:
                setattr(func, k, staticmethod(wipe_logger(v.__func__)))
        return func

    load_global = dis.opmap['LOAD_GLOBAL']
    nop = dis.opmap['NOP']
    call_method = dis.opmap['CALL']

    bytecode = list(func.__code__.co_code)
    mode = 0
    for n, byte in enumerate(bytecode[::2]):
        op = byte
        i = n * 2
        arg = bytecode[i + 1]
        if mode == 0:
            if op == load_global and func.__code__.co_names[arg>>1] == "logger":
                bytecode[i] = nop
                mode = 1
        elif mode == 1:
            bytecode[i] = nop
            if op == call_method:
                bytecode[i + 2] = nop
                mode = 0

    return types.FunctionType(
        types.CodeType(
            func.__code__.co_argcount,
            func.__code__.co_posonlyargcount,
            func.__code__.co_kwonlyargcount,
            func.__code__.co_nlocals,
            func.__code__.co_stacksize,
            func.__code__.co_flags,
            bytes(bytecode),
            func.__code__.co_consts,
            func.__code__.co_names,
            func.__code__.co_varnames,
            func.__code__.co_filename,
            func.__code__.co_name,
            func.__code__.co_qualname,
            func.__code__.co_firstlineno,
            func.__code__.co_linetable,
            func.__code__.co_exceptiontable,
            func.__code__.co_freevars,
            func.__code__.co_cellvars,
        ),
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__,
    )
"""