from __future__ import annotations

import re
import textwrap
import typing
from collections import defaultdict
import ast
from dataclasses import dataclass
import shutil
import json
import os
from os import PathLike
from contextlib import contextmanager

import sass

from pantra.components.render.renderer_base import StrOrCode
from pantra.components.render.render_node import RE_JS_VARS, RenderNode
from pantra.components.template import NodeType, AttrType, MacroCode, MacroType, collect_template, collect_styles, \
    get_template_path, HTMLTemplate
from pantra.jsmap.gen import make_js_bundle, JS_BUNDLE_FILENAME, JS_BUNDLE_MAP_FILENAME
from pantra.settings import config
from pantra.compiler import CodeMetrics

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.components.context import *

__all__ = ['CacheBuilder']

CI = 'x_'
CTX = f'{CI}.x'

class NameTransformer(ast.NodeTransformer):
    def __init__(self, new_name: str):
        self.new_name = new_name

    def visit_Name(self, node):
        self.generic_visit(node)
        if node.id == 'this':
            new_node = ast.Name(self.new_name, node.ctx)
            return ast.copy_location(new_node, node)
        return node

class ImportTransformer(ast.NodeTransformer):
    def __init__(self):
        self.cached_package_name = str(config.CACHE_PATH.relative_to(config.BASE_PATH)).replace(os.sep, ".")
        self.affected_names: dict[str, str] = {}

    def visit_ImportFrom(self, node):
        self.generic_visit(node)
        if node.module.startswith("components."):
            new_node = ast.ImportFrom(
                module=node.module.replace("components.", f"{self.cached_package_name}.", 1),
                names=node.names,
                level=node.level,
            )
            self.affected_names[node.module] = new_node.module
            return ast.copy_location(new_node, node)
        if node.module.startswith("apps."):
            new_node = ast.ImportFrom(
                module=node.module.replace("apps.", f"{self.cached_package_name}.apps.", 1),
                names=node.names,
                level=node.level,
            )
            self.affected_names[node.module] = new_node.module
            return ast.copy_location(new_node, node)
        return node

    def visit_Import(self, node):
        self.generic_visit(node)
        for alias in node.names:
            if alias.name.startswith("components.") or alias.name.startswith("apps."):
                break
        else:
            return node
        new_names = []
        for alias in node.names:
            if alias.name.startswith("components."):
                new_names.append(alias.name.replace("components.", f"{self.cached_package_name}.core.", 1))
                self.affected_names[alias.name] = new_names[-1]
            elif alias.name.startswith("apps."):
                new_names.append(alias.name.replace("apps.", f"{self.cached_package_name}.apps.", 1))
                self.affected_names[alias.name] = new_names[-1]
            else:
                new_names.append(alias.name)
        new_node = ast.Import(names=new_names)
        return ast.copy_location(new_node, node)

@dataclass
class LoopFunc:
    var_name: str
    body: str
    else_body: str = None

@dataclass
class SetFunc:
    var_name: str
    body: str

def next_node_name(parent: str) -> str:
    m = re.search(r"(.+?)(\d+)", parent)
    if m is None:
        return f'{parent}2'
    num = int(m.group(2))+1
    return f'{m.group(1)}{num}'

def indent(s: str, tabs_amount: int) -> str:
    return textwrap.indent(s, '    ' * tabs_amount)

def remix_this(s, new_name):
    tree = ast.parse(s)
    new_tree = NameTransformer(new_name).visit(tree)
    return ast.unparse(new_tree)

def makeup_func(macro_prefix: str, macro: StrOrCode, node: str = None) -> str:
    if macro_prefix == 'eval':
        return remix_this(macro.src, node)
    elif macro_prefix == 'js':
        return macro
    else:
        return macro.src

HELPERS_COPIED: set[PathLike] = set()
def remix_imports(s):
    tree = ast.parse(s)
    transformer = ImportTransformer()
    new_tree = transformer.visit(tree)
    for module_name, new_module_name in transformer.affected_names.items():
        src_file = (config.BASE_PATH / module_name.replace(".", os.sep)).with_suffix('.py')
        if src_file in HELPERS_COPIED:
            continue
        HELPERS_COPIED.add(src_file)
        dest_file = (config.BASE_PATH / new_module_name.replace(".", os.sep)).with_suffix('.py')
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        #shutil.copy(src_file, dest_file)
        src = src_file.read_text(encoding='utf-8')
        dest_file.write_text(remix_imports(src), encoding='utf-8')
    return ast.unparse(new_tree)

class CacheBuilder:
    templates_ready: set[str] = set()

    def __init__(self, app: str):
        self.app: str  = app
        self.funcs: dict[str, str | LoopFunc | SetFunc] = {}
        self.in_loop_body: int = 0
        self.python_code: str = ""
        self.code_metrics: CodeMetrics = CodeMetrics()
        self.prefixes: dict[str, int] = defaultdict(int)
        self.current_react_vars: set[str] = set()

    def collect_styles(self):
        print("Collecting styles...")
        dest_path = config.CACHE_PATH / 'css'
        dest_path.mkdir(parents=True, exist_ok=True)
        # normalize.css
        shutil.copy(config.CSS_PATH / 'normalize.css', dest_path)
        # basic.scss
        text = (config.CSS_PATH / 'basic.scss').read_text(encoding='utf-8')
        css = sass.compile(string=text, output_style='compact', include_paths=[str(config.CSS_PATH.parent)])
        (dest_path / 'basic.css').write_text(css, encoding='utf-8')
        # global.css
        print(f"    Collecting common styles...")
        styles = collect_styles('Core', config.COMPONENTS_PATH, print)
        (dest_path / 'global.css').write_text(styles, encoding='utf-8')
        # local css
        print(f"    [{self.app}] Collecting local styles...")
        app_path = config.APPS_PATH / self.app
        styles = collect_styles(self.app, app_path, print)
        (dest_path / f'{self.app}.local.css').write_text(styles, encoding='utf-8')

    def collect_js(self):
        print("Building JS bundle...")
        dest_path = config.CACHE_PATH / 'js'
        dest_path.mkdir(parents=True, exist_ok=True)
        config_line = json.dumps({
            k: v
            for k, v in config.__dict__.items() if k.startswith('JS_') and type(v) in (str, int, float, bool)
        })
        content, map = make_js_bundle(config.JS_PATH, config_line=config_line, with_content=True)
        (dest_path / JS_BUNDLE_FILENAME).write_text(content, encoding='utf-8')
        (dest_path / JS_BUNDLE_MAP_FILENAME).write_text(map, encoding='utf-8')

    def collect_static(self):
        print("Collecting static files...")
        # copy bootstrap
        src_path = config.BOOTSTRAP_FILENAME
        dest_path = config.CACHE_PATH / config.BOOTSTRAP_FILENAME.name
        shutil.copy(src_path, dest_path)
        # copy static from `components`
        src_path = config.COMPONENTS_PATH / config.STATIC_DIR
        dest_path = config.CACHE_PATH / config.STATIC_DIR
        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        # copy static from each component
        for template_name in self.templates_ready:
            t = collect_template(template_name, app=self.app)
            if (src_path := config.BASE_PATH / get_template_path(t) / config.STATIC_DIR).exists():
                shutil.copytree(src_path, dest_path / f'${template_name}', dirs_exist_ok=True)
        # copy static from app
        if (src_path := config.APPS_PATH / self.app / config.STATIC_DIR).exists():
            shutil.copytree(src_path, dest_path / f'~{self.app}', dirs_exist_ok=True)

    def collect_locale(self):
        print("Collecting locale...")
        # core locale
        src_path = config.COMPONENTS_PATH / 'locale'
        dest_path = config.CACHE_PATH / 'core' / 'locale'
        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        # app locale
        src_path = config.APPS_PATH / self.app / 'locale'
        dest_path = config.CACHE_PATH / 'apps' / self.app / 'locale'
        if src_path.exists():
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

    def collect_data(self):
        print("Collecting data...")
        src_path = config.APPS_PATH / self.app / 'data'
        dest_path = config.CACHE_PATH / 'apps' / self.app / 'data'
        if src_path.exists():
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

    def gen_prefix(self, prefix: str='') -> str:
        self.prefixes[prefix] += 1
        return prefix + "_" + str(self.prefixes[prefix])

    def translate(self, s: str) -> str:
        if s.startswith('\\'):
            return repr(s[1:])
        if s.startswith('#'):
            return f'_({s[1:]!r})'
        return repr(s)

    def build_value(self, source: StrOrCode, node: str) -> str:
        if isinstance(source, str):
            if source.startswith('@'):
                return source[1:]
            return self.translate(source)
        if type(source) is MacroCode:
            if source.reactive:
                self.current_react_vars.update(source.vars)
            if type(source.code) == list:
                if len(source.code) == 1:
                    value = source.code[0]
                else:
                    value = '.'.join(source.code)
            else:
                return makeup_func("eval", source, node)
                #macros = self.reg_macros('func', source)
                # argument `this`
                #value = f'{macros}({node})'

            if source.type == MacroType.STRING:
                return value + " or ''"
            return value
        return repr(source)

    def build_func(self, source: StrOrCode, node: str, var_list: str = '') -> str:
        if isinstance(source, str):
            return f'lambda {var_list}: {source}'
        if type(source) is MacroCode:
            #if source.reactive:
            #    self.current_react_vars.update(source.vars)
            return f'lambda {var_list}: '+self.build_value(source, node)
        raise ValueError("Can't build a function with raw value")

    def dynamic_string(self, source: StrOrCode, node: str) -> str:
        if type(source) is MacroCode:
            return f'{CI}.DynamicString({self.build_func(source, node)})'
        return repr(source)

    def dynamic_value(self, source: Any | MacroCode, node: str) -> str:
        if type(source) is MacroCode:
            return f'{CI}.DynamicValue({self.build_func(source, node)})'
        return self.translate(source)

    def dynamic_string_i10n(self, source: StrOrCode, node: str) -> str:
        if type(source) is MacroCode:
            return f'{CI}.DynamicString({self.build_func(source, node)})'
        return self.translate(source)

    def arrange_the_block(self, node: RenderNode, template) -> str:
        # we have to render control nodes as Stubs to hold middle DOM position
        if node and node.render_if_necessary:
            if (node.index() < len(template.parent.children) - 1
                and node.context.locals.has_reactions_to(node)):
                return 'self.arrange_the_block(node)'
        return ''

    def collect_react_vars(self, node: str) -> str:
        if self.current_react_vars:
            vars = ', '.join(repr(v) for v in self.current_react_vars)
            self.current_react_vars = set()
            return f'self.ctx.locals.register_reactions({{{vars}}}, {node})\n'
        return ''

    @contextmanager
    def sub_context(self):
        save_funcs = self.funcs
        self.funcs = {}
        self.in_loop_body += 1
        yield
        self.in_loop_body -= 1
        self.funcs = save_funcs

    def func_ctx_prefix(self):
        return "self." if self.in_loop_body == 0 else ""

    def collect_funcs(self) -> str:
        self_var_name = 'self, ' if self.in_loop_body==0 else ''

        funcs = []
        for k, v in self.funcs.items():
            if type(v) is LoopFunc:
                funcs.append(f'def {k}({self_var_name}node, forloop, {v.var_name}):\n{indent(v.body, 1)}')
                if v.else_body is not None:
                    funcs.append(f'def {k}_else({self_var_name}node):\n{indent(v.else_body, 1)}')
            elif type(v) is SetFunc:
                funcs.append(f'def {k}({self_var_name}node, {v.var_name}):\n{indent(v.body, 1)}')
            else:
                funcs.append(f'def {k}({self_var_name}node):\n{indent(v, 1)}')
        return '\n'.join(funcs)

    #region Attributes processor

    @staticmethod
    def _return_false(*args):
        return None

    @staticmethod
    def _return_true(*args):
        return ''

    def _process_attr_ref_name(self, attr_name, value, node):
        res = f"self.ctx.refs[{attr_name!r}] = {node}\n"
        res += f"{node}.ref_name = {attr_name!r}\n"
        return res

    def _process_attr_cref_name(self, attr_name, value, node):
        res = f"self.ctx.refs[{attr_name!r}] = {node}.locals\n"
        return res

    def _process_attr_scope(self, attr_name, value, node):
        res = f"{node}.scope[{attr_name!r}] = {self.build_value(value, node)}\n"
        return res

    def _process_attr_on_init(self, attr_name, value, node):
        #res = f"{CI}.run_safe(self.ctx, lambda: {value}({node}), dont_refresh=True)\n"
        res = f"{value}({node})\n"
        return res

    def _process_attr_class_switch(self, attr_name, value, node):
        if value is None:
            value = attr_name
        func = self.build_func(value, node)
        res = f"{node}.con_classes.append(({func}, {attr_name!r}))\n"
        return res

    def _process_attr_dynamic_style(self, attr_name, value, node):
        if value is None:
            value = MacroCode(MacroType.STRING, False, None, attr_name)
        res = f"{node}.style[{attr_name!r}] = {self.dynamic_string(value, node)}\n"
        return res

    def _process_attr_bind_value(self, attr_name, value, node):
        if value is None:
            value = 'value'
        res = f"{node}.attributes['bind:value'] = {value!r}\n"
        res += f"{node}.value = {value}\n"
        res += f'self.ctx.locals.register_reactions({{{value!r}}}, {node})\n'
        return res

    def _process_attr_dynamic_set(self, attr_name, value, node):
        if value is None:
            value = MacroCode(MacroType.STRING, False, None, attr_name)
        if attr_name in ('focus', 'localize'):
            if isinstance(value, str) and value == "yes":
                value = 'True'
            elif isinstance(value, str) and value == "no":
                value = 'False'
            else:
                value = self.build_value(value, node)
            if attr_name == 'focus':
                res = f'{node}._set_focused = bool({value})\n'
            else:
                res = f'{node}.localize = bool({value})\n'
        elif attr_name == 'type':
            res = f'{node}.value_type = {self.build_value(value, node)}\n'
        else:
            res = f'{node}.attributes[{attr_name!r}] = {self.dynamic_string(value, node)}\n'
        return res

    def _process_attr_dynamic_set_ctx(self, attr_name, value, node):
        res = ''
        if value is None:
            value = 'True'
        elif isinstance(value, str) and value == "yes":
            value = 'True'
        elif isinstance(value, str) and value == "no":
            value = 'False'
        else:
            value = self.dynamic_value(value, node)
            res = f'_value = {value!r}\n'
            res += f'{node}.attributes[{attr_name!r}] = _value\n'
            value = '_value.update()'
        res += f'{node}.locals[{attr_name!r}] = {value}\n'
        return res

    def _process_attr_data(self, attr_name, value, node):
        res = f'{node}.data[{attr_name!r}] = {self.build_value(value, node)}\n'
        return res

    def _process_attr_src_href(self, attr_name, value, node):
        if type(value) is MacroCode:
            value = self.build_value(value, node)
        else:
            value = repr(value)
        res = f"{node}.attributes[{attr_name!r}] = self.ctx.static({attr_name!r}, {value})\n"
        return res

    def _process_attr_style(self, attr_name, value, node):
        res = f"{node}.style = {self.dynamic_string(value, node)}\n"
        return res

    def _process_attr_class(self, attr_name, value, node):
        if type(value) is MacroCode:
            res = f"{node}.classes = {self.dynamic_string(value, node)}\n"
        else:
            res = f"{node}.classes = {CI}.DynamicClasses({value!r})\n"
        return res

    def _process_attr_type(self, attr_name, value, node):
        res = f"{node}.value_type = {self.build_value(value, node)}\n"
        return res

    def _process_attr_value(self, attr_name, value, node):
        res = f"{node}.value = {self.build_value(value, node)}\n"
        return res

    def _process_attr_localize(self, attr_name, value, node):
        res = f"{node}.localize = bool({self.build_value(value, node)})\n"
        return res

    def _process_attr_set_false_ctx(self, attr_name, value, node):
        res = f"{node}.locals[{attr_name!r}] = False\n"
        return res

    def _process_attr_consume(self, attr_name, value, node):
        if value is not None:
            if value == '*':
                res = f'{node}.locals |= {node}.context.locals\n'
            else:
                res = ''
                for at in value.split(','):
                    at = at.strip()
                    res += f'{node}.locals[{at!r}] = {at}\n'
        else:
            res = ''
        return res

    PROCESS_HTML_ATTR: dict[int, Callable[[Self, str, str, str], str | None]] = {
        AttrType.ATTR.value: _return_false,
        AttrType.REF_NAME.value: _process_attr_ref_name,
        AttrType.CREF_NAME.value: _process_attr_cref_name,
        AttrType.SCOPE.value: _process_attr_scope,
        AttrType.ON_RENDER.value: _return_true,
        AttrType.ON_INIT.value: _process_attr_on_init,
        AttrType.CLASS_SWITCH.value: _process_attr_class_switch,
        AttrType.DYNAMIC_STYLE.value: _process_attr_dynamic_style,
        AttrType.BIND_VALUE.value: _process_attr_bind_value,
        AttrType.DYNAMIC_SET.value: _process_attr_dynamic_set,
        AttrType.DATA.value: _process_attr_data,
        AttrType.SRC_HREF.value: _process_attr_src_href,
        AttrType.REACTIVE.value: _return_true,
        AttrType.STYLE.value: _process_attr_style,
        AttrType.CLASS.value: _process_attr_class,
        AttrType.TYPE.value: _process_attr_type,
        AttrType.VALUE.value: _process_attr_value,
        AttrType.LOCALIZE.value: _process_attr_localize,
        AttrType.SET_FALSE.value: _return_false,
        AttrType.CONSUME.value: _return_false,
    }

    PROCESS_CTX_ATTR: dict[int, Callable[[Self, str, str, str], str | None]] = {
        AttrType.ATTR.value: _return_false,
        AttrType.REF_NAME.value: _process_attr_ref_name,
        AttrType.CREF_NAME.value: _process_attr_cref_name,
        AttrType.SCOPE.value: _process_attr_scope,
        AttrType.ON_RENDER.value: _return_true,
        AttrType.ON_INIT.value: _process_attr_on_init,
        AttrType.CLASS_SWITCH.value: _return_false,
        AttrType.DYNAMIC_STYLE.value: _return_false,
        AttrType.BIND_VALUE.value: _return_false,
        AttrType.DYNAMIC_SET.value: _process_attr_dynamic_set_ctx,
        AttrType.DATA.value:  _return_false,
        AttrType.SRC_HREF.value:  _return_false,
        AttrType.REACTIVE.value: _return_false,
        AttrType.STYLE.value: _return_false,
        AttrType.CLASS.value: _return_false,
        AttrType.TYPE.value: _return_false,
        AttrType.VALUE.value: _return_false,
        AttrType.LOCALIZE.value: _return_false,
        AttrType.SET_FALSE.value: _process_attr_set_false_ctx,
        AttrType.CONSUME.value: _process_attr_consume,
    }
    #endregion

    def process_attribute_html(self, attr_type: tuple[AttrType, str | None], attr: str, value: StrOrCode, node: str) -> str:
        res = self.PROCESS_HTML_ATTR[attr_type[0].value](self, attr_type[1], value, node)
        if res is None:
            res = f'{node}.attributes[{attr!r}] = {value and self.dynamic_string_i10n(value, node) or "None"}\n'
        return res

    def process_attribute_ctx(self, attr_type: tuple[AttrType, str | None], attr: str, value: StrOrCode, node: str) -> str:
        res = self.PROCESS_CTX_ATTR[attr_type[0].value](self, attr_type[1], value, node)
        if res is None:
            if isinstance(value, str) or type(value) is MacroCode:
                value = self.dynamic_value(value, node)
            elif value is None:
                value = 'True'
            if value.startswith(f'{CI}.DynamicValue'):
                res = f'_value = {value}\n'
                res += f'{node}.attributes[{attr!r}] = _value\n'
                res += f'{node}.locals[{attr!r}] = _value.update()\n'
            else:
                res = f'{node}.locals[{attr!r}] = {value}\n'
        return res

    #region Node builders
    def _call_after_render(self, template, node) -> str:
        if (func_name := template.attributes.get('on:render')) is not None:
            #return f'{CI}.run_safe(self.ctx.session, lambda: self.ctx[{func_name!r}]({node}), dont_refresh=True)\n'
            return f'{func_name}({node})\n'
        return ''

    def _build_html_tag(self, template, parent):
        if 'not:render' in template.attributes:
            return ''

        node = next_node_name(parent)
        res = f'{node} = self.add("{template.tag_name}", parent={parent})\n'

        for attr, value in template.attributes.items():
            res += self.process_attribute_html(template.attr_specs[attr], attr, value, node)
        res += self.collect_react_vars(node)

        if self.code_metrics.has_node_processor:
            #res += f"{CI}.run_safe(self.ctx.session, lambda: node_processor({node}), dont_refresh=True)\n"
            res += f"node_processor({node})\n"

        if len(template.children) == 1:
            single_child = template.children[0]
            if single_child.tag_name == '@text':
                res += f'{node}.text = {self.translate(single_child.content)}\n'
            elif single_child.tag_name == '@macro':
                res += f'{node}.text = {self.dynamic_string(single_child.content, node)}\n'
                res += self.collect_react_vars(node)
            else:
                res += self.build_node(single_child, node)
        elif template.children:
            for child in template.children:
                res += self.build_node(child, node)

        res += self._call_after_render(template, node)

        return res

    def _build_template_tag(self, template, parent):
        node = next_node_name(parent)
        CacheBuilder(self.app).make(template.tag_name)

        if 'not:render' in template.attributes:
            return ''

        res = f'{node} = {CTX}.Context({template.tag_name!r}, {parent})\n'
        if template.attributes.get('consume', '') is None:
            res += f'{node}.attributes = {node}.context.attributes\n'
            res += f'{node}.locals = {node}.context.locals\n'
            res += f'{node}.refs = {node}.context.refs\n'

        # evaluate attributes
        for attr, value in template.attributes.items():
            res += self.process_attribute_ctx(template.attr_specs[attr], attr, value, node)
        res += self.collect_react_vars(node)

        # attach slots
        if template.children:
            slot_func_name = self.gen_prefix('slot')
            res += f'{node}.slot = {CTX}.Slot(self.ctx, $func$, $reuse$)\n'
            slot_template = HTMLTemplate('@component', 0, None)
            for child in template.children:
                if child.tag_name == 'section':
                    section_template = HTMLTemplate('@component', 0, None)
                    section_template.children.extend(child.children)
                    reuse = 'reuse' in child.attributes
                    if (name:=child.attributes.get('name')) is not None:
                        section_func_name = slot_func_name + "_" + name
                        if not reuse:
                            res += (f'{node}.slot[{name!r}] = '
                                    f'{CTX}.Slot(self.ctx, {self.func_ctx_prefix()}{section_func_name}, False)\n')
                        else:
                            res += f'{node}.slot[{name!r}] = {CTX}.Slot(self.ctx, None, True)\n'
                    else:
                        section_func_name = slot_func_name
                        if not reuse:
                            res = (res.
                                   replace('$func$', self.func_ctx_prefix()+slot_func_name).
                                   replace('$reuse$', 'False'))
                        else:
                            res = res.replace('$func$', 'None').replace('$reuse$', 'True')
                    if not reuse:
                        self.funcs[section_func_name] = self.build_node(section_template, 'node')
                else:
                    slot_template.append(child)
            if slot_template.children:
                res = (res.
                       replace('$func$', self.func_ctx_prefix()+slot_func_name).
                       replace('$reuse$', 'False'))
                self.funcs[slot_func_name] = self.build_node(slot_template, 'node')
            else:
                res = (res.
                       replace('$func$', "lambda node: None").
                       replace('$reuse$', 'False'))

        if self.code_metrics.has_node_processor:
            #res += f"{CI}.run_safe(self.ctx.session, lambda: node_processor({node}), dont_refresh=True)\n"
            res += f"node_processor({node})\n"

        res += f"{node}.renderer.build()\n"

        res += self._call_after_render(template, node)

        return res

    def _build_root_node(self, template, parent):
        node = 'node'
        res = f"{node} = self.ctx\n"

        for child in template.children:
            res += self.build_node(child, node)

        if self.code_metrics.has_on_render:
            #res += f'{CI}.run_safe(self.ctx.session, on_render, dont_refresh=True)\n'
            res += f'on_render()\n'

        return res

    def _build_group(self, template, parent):
        res = ''
        for child in template.children:
            res += self.build_node(child, parent)
        return res

    def _build_macro_if(self, template, parent):
        node = next_node_name(parent)
        res = f'{node} = {CTX}.ConditionNode({parent}, None)\n'
        for i, child_template in enumerate(template.children):  # type: HTMLTemplate
            if child_template.tag_name != '#else':
                func_prefix = self.gen_prefix('if')
                condition_func = self.build_func(child_template.attributes["condition"], node)
                res += f'{node}.conditions.append({CTX}.Condition({condition_func}, {self.func_ctx_prefix()}{func_prefix}))\n'
                res += self.collect_react_vars(node)
            else:
                func_prefix = self.gen_prefix('else')
                res += f'{node}.conditions.append({CTX}.Condition(lambda: True, {self.func_ctx_prefix()}{func_prefix}))\n'
            self.funcs[func_prefix] = self.build_node(child_template, 'node')
        res += f'self.update({node})\n'
        return res

    def _build_macro_for(self, template, parent):
        node = next_node_name(parent)
        func_prefix = self.gen_prefix('for')
        res = f'{node} = {CTX}.LoopNode({parent}, None)\n'
        res += f'{node}.loop_template = {self.func_ctx_prefix()}{func_prefix}\n'
        loop_template = template[0]
        res += f'{node}.var_name = {loop_template.attributes["var_name"]!r}\n'
        res += f'{node}.iterator = {self.build_func(loop_template.attributes["iter"], node)}\n'
        if (index_func:=loop_template.attributes.get('index_func')) is not None:
            res += f'{node}.index_func = {self.build_func(index_func, node, "forloop, "+loop_template.attributes["var_name"])}\n'
        res += self.collect_react_vars(node)

        with self.sub_context():
            loop_func = LoopFunc(
                loop_template.attributes['var_name'],
                self.build_node(loop_template, 'node'),
            )
            loop_func.body = self.collect_funcs() + loop_func.body

        if len(template.children) > 1:
            res += f'{node}.else_template = {self.func_ctx_prefix()}{func_prefix}_else\n'
            with self.sub_context():
                loop_func.else_body = self.build_node(template[1], 'node')
                loop_func.else_body = self.collect_funcs() + loop_func.else_body

        self.funcs[func_prefix] = loop_func

        res += f'self.update({node})\n'
        return res

    def _build_macro_set(self, template, parent):
        node = next_node_name(parent)
        func_prefix = self.gen_prefix('set')
        res = f'{node} = {CTX}.SetNode({parent}, {self.func_ctx_prefix()}{func_prefix})\n'
        res += f'{node}.var_name = {template.attributes["var_name"]!r}\n'
        res += f'{node}.value = {self.build_func(template.attributes["value"], node)}\n'
        res += f'self.update({node})\n'
        res += self.collect_react_vars(node)

        with self.sub_context():
            func_body = ''
            for child in template.children:
                func_body += self.build_node(child, 'node')
            set_func = SetFunc(template.attributes["var_name"], self.collect_funcs() + func_body)

        self.funcs[func_prefix] = set_func

        return res

    def _build_at_component(self, template, parent):
        res = ''
        if 'render' in template.attributes:
            renderer = template.attributes['render']
            res += f'{renderer}(parent)\n'

        for child in template.children:
            res += self.build_node(child, parent)
        return res

    def _build_at_slot(self, template, parent):
        name = template.attributes.get('name')
        if name:
            res = f"slot = {parent}.context.slot and {parent}.context.slot[{name!r}]\n"
        else:
            res = f"slot = {parent}.context.slot and {parent}.context.slot.get_top()\n"

        res += 'if slot:\n'
        res += indent("with self.override_ns_type(slot):\n", 1)
        res += indent(f"slot.template({parent})\n", 2)
        if template.children:
            res += "else:\n"
            for child in template.children:
                res += indent(self.build_node(child, parent), 1)

        res += self._call_after_render(template, parent)
        return res

    def _build_python_includes(self, template: HTMLTemplate, module: str):
        with open((template.filename.parent / module).with_suffix('.py'), "rt") as f:
            self.python_code += f'# include `{module}`\n'
            self.python_code += f.read()

    def _build_at_python(self, template, parent):
        if 'use' in template.attributes:
            for module in template.attributes['use'].strip('" \'').split():
                self._build_python_includes(template, module)

        self.python_code += '# python code'
        self.python_code += template.content.strip('\n#')
        self.python_code = self.python_code.replace('\r\n', '\n')
        self.python_code = remix_imports(self.python_code)
        self.code_metrics = CodeMetrics.collect(self.python_code)

        res = ''
        if self.code_metrics.has_init:
            res += (f'if init() is False:\n'
                    f'    raise {CI}.ContextInitFailed()\n')
        if self.code_metrics.has_on_restart:
            res += 'on_restart()\n'
        if self.code_metrics.has_ns_type:
            res += 'self.ctx.ns_type = ns_type\n'

        return res

    def _build_at_script(self, template, parent):
        def subst(matchobj) -> str:
            expr = matchobj.group(1)
            return '{'+self.build_value(expr, parent)+'}'

        text = 'f"' + RE_JS_VARS.sub(subst, template.content) + '"' if template.content else ""
        #func = self.reg_macros("js", text)
        func = makeup_func("js", text)
        res = f"{CTX}.ScriptNode({parent}, f'{{self.__class__.__name__}}_{template.index}', attributes={template.attributes!r}, text={func}())\n"
        return res

    def _build_at_style(self, template, parent):
        # styles collected elsewhere
        if 'global' not in template.attributes:
            res = 'self.ctx._restyle = True\n'
        else:
            res = ''
        return res

    def _build_at_event(self, template, parent):
        node = next_node_name(parent)
        res = f'{node} = EventNode({parent})\n'
        for k, v in template.attributes.items():
            if k == 'selector':
                if 'global' in template.attributes:
                    res += f'{node}.attributes[{k!r}] = {v!r}\n'
                else:
                    res += f"{node}.attributes[{k!r}] = {','.join(f'.{template.root.name} {s}' for s in v.split(','))!r}\n"
                    res += 'self.ctx._restyle = True\n'
            else:
                res += f'{node}.attributes[{k!r}] = {self.dynamic_string(v, node)}\n'
        return res

    def _build_at_scope(self, template, parent):
        res = 'scope = {}\n'
        for k, v in template.attributes.items():
            res += f'scope[{k!r}] = {self.build_value(v, parent)}\n'
        res += f'{parent}.set_scope(scope)\n'
        return res

    def _build_at_text(self, template, parent):
        res = f'{CTX}.TextNode({parent}, {self.translate(template.content)})\n'
        return res

    def _build_at_macro(self, template, parent):
        res = f'{CTX}.TextNode({parent}, {self.dynamic_string(template.content, parent)})\n'
        return res

    def _build_at_react(self, template, parent):
        var_name = template.attributes.get('to')
        action = template.attributes.get('action')
        if not var_name or not action:
            raise ValueError('<react> tag must have attributes `to` and `action`')
        node = next_node_name(parent)
        res = f'{node} = {CTX}.ReactNode({parent}, {var_name!r}, {action!r})\n'
        # take in account consumed contexts
        res += f'self.ctx.locals.register_reactions({{ {var_name} }}, {node})\n'
        return res

    NODE_BUILDERS: dict[int, Callable[[Self, HTMLTemplate, str], str]] = {
        NodeType.HTML_TAG.value: _build_html_tag,
        NodeType.TEMPLATE_TAG.value: _build_template_tag,
        NodeType.ROOT_NODE.value: _build_root_node,
        NodeType.MACRO_IF.value: _build_macro_if,
        NodeType.MACRO_FOR.value: _build_macro_for,
        NodeType.MACRO_SET.value: _build_macro_set,
        NodeType.MACRO_INTERNAL.value: _build_group,
        NodeType.AT_COMPONENT.value: _build_at_component,
        NodeType.AT_SLOT.value: _build_at_slot,
        NodeType.AT_PYTHON.value: _build_at_python,
        NodeType.AT_SCRIPT.value: _build_at_script,
        NodeType.AT_STYLE.value: _build_at_style,
        NodeType.AT_EVENT.value: _build_at_event,
        NodeType.AT_SCOPE.value: _build_at_scope,
        NodeType.AT_TEXT.value: _build_at_text,
        NodeType.AT_MACRO.value: _build_at_macro,
        NodeType.AT_REACT.value: _build_at_react,
    }
    #endregion

    def build_node(self, template: HTMLTemplate, parent: str) -> str:
        res = ''
        if (node_name := template.attributes.get('data-node')) is not None:
            res += f'data_node = {CTX}.RenderNode("data-node", None, {CI}.NullContextShot(), {parent}.session)\n'
            res += f'data_node.context = {parent}.context\n'
            res += "if not self.ctx.data_nodes:\n"
            res += "    self.ctx.data_nodes = {}\n"
            res += f"self.ctx.data_nodes[{node_name!r}] = data_node\n"
            parent = "data_node"
        return res + self.NODE_BUILDERS[template.node_type.value](self, template, parent)

    def make(self, template_name: str):
        if template_name in self.templates_ready:
            return

        print(f'    {template_name}')

        template = collect_template(template_name, app=self.app)
        code = self.build_node(template, 'None')

        funcs = self.collect_funcs()

        result = CACHED_CONTENT.format(
            template_name=template_name,
            funcs=indent(funcs, 1),
            build_code=indent(code, 2),
            python_code=self.python_code,
        )

        result = result.replace("    \n    \n", "\n")

        if template.filename.is_relative_to(config.APPS_PATH):
            (config.CACHE_PATH / 'apps' / self.app).mkdir(parents=True, exist_ok=True)
            (config.CACHE_PATH / 'apps' / self.app / template.name).with_suffix('.py').write_text(result, encoding='utf-8')
        else:
            (config.CACHE_PATH / 'core').mkdir(parents=True, exist_ok=True)
            (config.CACHE_PATH / 'core' / template.name).with_suffix('.py').write_text(result, encoding='utf-8')

        self.templates_ready.add(template.name)

CACHED_CONTENT = f"""# This is cached component's code, don't edit directly !!!
import pantra.cached.imports as {CI}

class {{template_name}}Renderer({CI}.RendererCached):
    __slots__ = ()
{{funcs}}
    def build_node(self, template, parent = None):
{{build_code}}
        
{{python_code}}
"""
