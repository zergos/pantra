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
    from .settings import safe_config
    if not safe_config.WIPE_LOGGING:
        return func

    source_lines, line_num = inspect.getsourcelines(func)
    source = '\n' * (line_num-1) + textwrap.dedent(''.join(source_lines))
    tree = ast.parse(source)
    func_name = tree.body[0].name
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

