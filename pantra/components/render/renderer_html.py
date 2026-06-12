from __future__ import annotations

import sys
import typing

from pantra.common import typename, DynamicStyles, DynamicClasses
from pantra.compiler import ContextInitFailed, compile_context_code
from pantra.settings import config
from ..template import AttrType, NodeType, collect_template, MacroCode, MacroType
from ..context import HTMLElement, Context, Slot, ConditionNode, Condition, LoopNode, SetNode, ScriptNode, \
    EventNode, TextNode, ReactNode
from ..shot import NullContextShot
from .renderer_base import RendererBase, ValueOrCode, ForLoopType
from .render_node import RenderNode

if typing.TYPE_CHECKING:
    from typing import *
    from pathlib import Path
    from pantra.session import Session
    from ..template import HTMLTemplate

class RendererHTML(RendererBase):
    """Renderer from HTML-like files"""

    templates: ClassVar[dict[str, HTMLTemplate | None]] = {}

    @staticmethod
    def _search_component(path: Path, name: str) -> Path | None:
        for file in path.glob(f"**/{name}.html"):
            return file
        return None

    @classmethod
    def collect_template(cls, name: str, session: Optional[Session] = None, app: Optional[str] = None) -> Optional[HTMLTemplate]:
        app = session and session.app or app
        key = app + '/' + name if app is not None else name
        if key in cls.templates:
            return cls.templates[key]

        path = app and cls._search_component(config.APPS_PATH / app, name)
        if not path:
            if name in cls.templates:
                cls.templates[key] = cls.templates[name]
                return cls.templates[name]
            # elif config.PRODUCTIVE:
            #    templates[key] = None
            #    return None

            path = cls._search_component(config.COMPONENTS_PATH, name)
            if not path:
                cls.templates[key] = None
                return None
            key = name

        from ..loader import load
        template = load(path, session.error) if session is not None else load(path, lambda s: print(s, file=sys.stderr))
        if template:
            template.name = name
            cls.templates[key] = template
        return template

    def arrange_the_block(self, node: RenderNode, template):
        # we have to render control nodes as Stubs to hold middle DOM position
        if (node.index() < len(template.parent.children) - 1
            and node.context.locals.has_reactions_to(node)):
            node.render_this_node = True
            self.ctx.shot += node

    #region Attribute processors
    @staticmethod
    def _return_false(*args):
        return False

    @staticmethod
    def _return_true(*args):
        return True

    def _process_attr_ref_name(self, attr_name, value, node):
        self.ctx.refs[attr_name] = node
        node.ref_name = attr_name
        return True

    def _process_attr_cref_name(self, attr_name, value, node):
        if typename(node) != 'Context':
            self.ctx.session.error('Use cref: with components only')
            return True
        self.ctx.refs[attr_name] = node.locals
        return True

    def _process_attr_scope(self, attr_name, value, node):
        node.scope[attr_name] = self.makeup_value(value, node)
        return True

    def _process_attr_on_init(self, attr_name, value, node):
        #run_safe(self.ctx.session, lambda: self.ctx[value](node), dont_refresh=True)
        self.ctx[value](node)
        return True

    def _process_attr_class_switch(self, attr_name, value, node):
        if value is None:
            value = MacroCode(MacroType.VALUE, False, False, None, attr_name)
        node.classes[attr_name] = self.makeup_value(value, node)
        return True

    def _process_attr_dynamic_style(self, attr_name, value, node):
        if value is None:
            value = MacroCode(MacroType.STRING, False, False, None, attr_name)
        node.style[attr_name] = self.makeup_value(value, node)
        return True

    def _process_attr_bind_value(self, attr_name, value, node):
        if value is None:
            value = 'value'
        node.attributes['bind:value'] = value
        node.value = self.ctx.locals[value]
        self.ctx.locals.register_reactions({value}, node)
        return True

    def _process_attr_dynamic_set(self, attr_name, value, node):
        if value is None:
            value = MacroCode(MacroType.STRING, False, False, None, attr_name)
        if attr_name in ('focused', 'localize'):
            if isinstance(value, str) and value == "yes":
                value = True
            elif isinstance(value, str) and value == "no":
                value = False
            else:
                value = self.makeup_value(value, node, True)
            if attr_name == 'focused':
                node._set_focused = bool(value)
            else:
                node.localize = bool(value)
        elif attr_name == 'type':
            node.value_type = self.makeup_value(value, node, True)
        else:
            node.attributes[attr_name] = self.makeup_value(value, node)
        return True

    def _process_attr_dynamic_set_ctx(self, attr_name, value, node):
        if value is None:
            value = True
        elif isinstance(value, str) and value == "yes":
            value = True
        elif isinstance(value, str) and value == "no":
            value = False
        elif isinstance(value, MacroCode):
            node.attributes[attr_name] = self.makeup_value(value, node)
            value = node.attributes[attr_name]
        node.locals[attr_name] = value
        return True

    def _process_attr_data(self, attr_name, value, node):
        node.data[attr_name] = self.makeup_value(value, node)
        return True

    def _process_attr_src_href(self, attr_name, subdir, value, node):
        node.attributes[attr_name] = (
            self.ctx.static(subdir, self.makeup_value(value, node, True)
            if type(value) is MacroCode else value))
        return True

    def _process_attr_style(self, attr_name, value, node):
        expr = self.makeup_value(value, node)
        if type(value) is MacroCode:
            node.style['$'] = expr
        else:
            node.style += expr
        return True

    def _process_attr_class(self, attr_name, value, node):
        expr = self.makeup_value(value, node)
        if type(value) is MacroCode:
            node.classes['$'] = expr
        else:
            node.classes += expr
        return True

    def _process_attr_type(self, attr_name, value, node):
        node.value_type = self.makeup_value(value, node, True)
        return True

    def _process_attr_value(self, attr_name, value, node):
        node.value = self.makeup_value(value, node, True)
        return True

    def _process_attr_localize(self, attr_name, value, node):
        node.localize = bool(self.makeup_value(value, node, True))
        return True

    def _process_attr_set_false_ctx(self, attr_name, value, node):
        node.locals[attr_name] = False
        return True

    def _process_attr_consume(self, attr_name, value, node):
        if value is not None:
            if value == '*':
                node.locals |= node.context.locals
            else:
                for at in value.split(','):
                    at = at.strip()
                    # copy local values into consumed context
                    if at in node.context.locals:
                        node.locals[at] = node.context[at]
        return True

    PROCESS_HTML_ATTR: dict[int, Callable[[Self, str, Any, HTMLElement], bool]] = {
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
        AttrType.SRC.value: lambda self, *args: self._process_attr_src_href("src", *args),
        AttrType.HREF.value: lambda self, *args: self._process_attr_src_href("href", *args),
        AttrType.REACTIVE.value: _return_true,
        AttrType.STYLE.value: _process_attr_style,
        AttrType.CLASS.value: _process_attr_class,
        AttrType.TYPE.value: _process_attr_type,
        AttrType.VALUE.value: _process_attr_value,
        AttrType.LOCALIZE.value: _process_attr_localize,
        AttrType.SET_FALSE.value: _return_false,
        AttrType.CONSUME.value: _return_false,
        AttrType.DATA_NODE.value: _return_true,
    }

    PROCESS_CTX_ATTR: dict[int, Callable[[Self, str, Any, Context], bool]] = {
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
        AttrType.SRC.value:  _return_false,
        AttrType.HREF.value: _return_false,
        AttrType.REACTIVE.value: _return_false,
        AttrType.STYLE.value: _return_false,
        AttrType.CLASS.value: _return_false,
        AttrType.TYPE.value: _return_false,
        AttrType.VALUE.value: _return_false,
        AttrType.LOCALIZE.value: _return_false,
        AttrType.SET_FALSE.value: _process_attr_set_false_ctx,
        AttrType.CONSUME.value: _process_attr_consume,
        AttrType.DATA_NODE.value: _return_false,
    }
    #endregion

    def process_special_attribute_html(self, attr: tuple[AttrType, str | None], value: ValueOrCode, node: Union[HTMLElement, Context]) -> bool:
        return self.PROCESS_HTML_ATTR[attr[0].value](self, attr[1], value, node)

    def process_special_attribute_ctx(self, attr: tuple[AttrType, str | None], value: ValueOrCode, node: Union[HTMLElement, Context]) -> bool:
        return self.PROCESS_CTX_ATTR[attr[0].value](self, attr[1], value, node)

    #region Node builders
    def _call_after_render(self, template, node):
        if (func_name := template.attributes.get('on:render')) is not None:
            if func_name not in self.ctx.locals:
                raise ValueError(f'No renderer named `{func_name}` found in `{self.ctx.template.name}`')
            #run_safe(self.ctx.session, lambda: self.ctx[func_name](node), dont_refresh=True)
            self.ctx[func_name](node)

    def _build_group(self, template, parent):
        for child in template.children:
            self.build_node(child, parent)

    def _build_html_tag(self, template, parent):
        if 'not:render' in template.attributes:
            # forget it
            return None

        node = self.add(template.tag_name, parent=parent)

        # evaluate attributes
        for attr, value in template.attributes.items():
            if not self.process_special_attribute_html(template.attr_specs[attr], value, node):
                node.attributes[attr] = self.makeup_value(value, node)

        # evaluate body
        if self.ctx.code_metrics.has_node_processor:
            #run_safe(self.ctx.session, lambda: self.ctx['node_processor'](node), dont_refresh=True)
            self.ctx['node_processor'](node)

        # evaluate children
        if len(template.children) == 1:
            single_child = template.children[0]
            if single_child.tag_name == '@text':
                node.attributes['$'] = self.makeup_value(single_child.content, node)
                node.text = node.attributes['$']
            else:
                self.build_node(single_child, node)
        else:
            self._build_group(template, node)

        self._call_after_render(template, node)
        return node

    def _build_at_text(self, template, parent):
        node = TextNode(parent, self.makeup_value(template.content, parent))
        return node

    def _build_template_tag(self, template, parent):
        node_template = collect_template(template.tag_name, self.ctx.session)

        if not node_template: return None

        if 'not:render' in template.attributes:
            return None

        node = Context(template.tag_name, parent)
        if template.attributes.get('consume', '') is None:
            node.attributes = node.context.attributes
            node.locals = node.context.locals
            #for k in ('init', 'on_restart'):
            #    if k in node.locals:
            #        del node.locals[k]
            node.refs = node.context.refs

        # evaluate attributes
        for attr, value in template.attributes.items():
            if not self.process_special_attribute_ctx(template.attr_specs[attr], value, node):
                if value is None:
                    value = True
                elif type(value) is MacroCode:
                    node.attributes[attr] = self.makeup_value(value, node)
                    value = node.attributes[attr]
                node.locals[attr] = value

        # attach slots
        if template.children:
            node.slot = Slot(self.ctx, template, False)
            for child in template.children:
                if child.tag_name == 'section':
                    if name := child.attributes.get('name'):
                        node.slot[name] = Slot(self.ctx, child, 'reuse' in child.attributes)
                    else:
                        node.slot.template = child
                        node.slot.for_reuse = 'reuse' in child.attributes

        if self.ctx.code_metrics.has_node_processor:
            #run_safe(self.ctx.session, lambda: self.ctx['node_processor'](node), dont_refresh=True)
            self.ctx['node_processor'](node)

        try:
            node.renderer.build()
        except ContextInitFailed:
            node.remove()
            return None

        self._call_after_render(template, node)

        return node

    def _build_root_node(self, template, parent):
        node = self.ctx

        #if template.children and template.children[0].tag_name != "@python":
            # we have no python script here, so, we need to make `locals` from `attributes` directly
        #    node.locals.update(node.attributes)

        self._build_group(template, node)

        if self.ctx.code_metrics.has_on_render:
            #run_safe(self.ctx.session, self.ctx["on_render"], dont_refresh=True)
            self.ctx["on_render"]()

        return node

    def _build_macro_if(self, template, parent):
        node = ConditionNode(parent, template, self)
        for child_template in template.children:  # type: HTMLTemplate
            if child_template.tag_name != '#else':
                item = Condition(self.makeup_value(child_template.attributes['condition'], node), child_template)
            else:
                item = Condition((lambda: True), child_template)
            node.conditions.append(item)

        self.arrange_the_block(node, template)
        self.update(node)
        return node

    def _build_macro_for(self, template, parent):
        node: LoopNode = LoopNode(parent, template, self)
        loop_template = template[0]
        node.var_name = loop_template.attributes['var_name']
        node.iterator = self.makeup_value(loop_template.attributes['iter'], node)
        if (index_func:=loop_template.attributes.get('index_func')) is not None:
            node.index_func = self.makeup_value(index_func, node)

        node.loop_template = loop_template
        if len(template.children) > 1:
            node.else_template = template[1]

        self.arrange_the_block(node, template)
        self.update(node)
        return node

    def _build_macro_set(self, template, parent):
        node: SetNode = SetNode(parent, template, self)
        for k, v in template.attributes.items():
            node.variables[k] = self.makeup_value(v, node)
        node.scoped = template.tag_name == '#set:scope'
        node.self_clear = template.tag_name == '#set:clear'

        self.update(node)

        if not node.self_clear:
            self._build_group(template, node)

        return node

    def _build_at_component(self, template, parent):
        if 'render' in template.attributes:
            renderer = template.attributes['render']
            if renderer not in self.ctx.locals:
                self.ctx.session.error(f'component renderer {renderer} not found')
                return None
            self.ctx.locals[renderer](parent)

        self._build_group(template, parent)
        return None

    def _build_at_slot(self, template, parent):
        if (name := template.attributes.get('name')) is not None:
            slot: Slot = parent.context.slot and parent.context.slot[name]
        else:
            slot: Slot = parent.context.slot.get_top()

        if not slot:
            self._build_group(template, parent)
            self._call_after_render(template, parent)
            return parent

        with self.override_ns_type(slot):
            for child in slot.template.children:
                if not name and child.tag_name == 'section':
                    continue
                #self.build_node(child, parent)
                slot.ctx.renderer.build_node(child, parent)

        self._call_after_render(template, parent)
        return None

    def _build_at_python(self, template, parent):
        if not self.ctx._executed:
            self.ctx._executed = True
            compile_context_code(self.ctx, template)
            self.ctx.code_metrics = template.code_metrics
        return parent

    def _build_at_script(self, template, parent):
        attributes = template.attributes.copy()
        put_to_head = attributes.pop('location', 'head') == 'head'
        node = ScriptNode(parent, f'{self.ctx.template.name}_{template.script_index}',
                          attributes,
                          self.makeup_value(template.content, parent, True),
                          put_to_head)
        return node

    def _build_at_style(self, template, parent):
        # styles collected elsewhere
        if 'global' not in template.attributes:
            self.ctx._restyle = True
        return parent

    def _build_at_event(self, template, parent):
        node = EventNode(parent)
        for k, v in template.attributes.items():
            if k == 'selector':
                if 'global' in template.attributes:
                    node.selector = v
                else:
                    node.selector = ','.join(f'.{self.ctx.template.name} {s}' for s in v.split(','))
                    self.ctx._restyle = True
            elif k.startswith('on:'):
                node.events[k] = self.makeup_value(v, node)
        return node

    def _build_at_react(self, template, parent):
        var_name = template.attributes.get('to')
        action = template.attributes.get('action')
        if not var_name:
            self.ctx.session.error('<react> tag must have attributes `to`')
            return None
        node = ReactNode(parent, var_name, action)
        # take in account consumed contexts
        self.ctx.locals.register_reactions(set(v.strip() for v in var_name.split(',')), node)

        self._build_group(template, node)

        return node

    NODE_BUILDERS: dict[int, Callable[[Self, HTMLTemplate, RenderNode], RenderNode]] = {
        NodeType.HTML_TAG.value: _build_html_tag,
        NodeType.AT_TEXT: _build_at_text,
        NodeType.TEMPLATE_TAG.value: _build_template_tag,
        NodeType.ROOT_NODE.value: _build_root_node,
        NodeType.MACRO_IF.value: _build_macro_if,
        NodeType.MACRO_FOR.value: _build_macro_for,
        NodeType.MACRO_SET.value: _build_macro_set,
        NodeType.AT_COMPONENT.value: _build_at_component,
        NodeType.AT_SLOT.value: _build_at_slot,
        NodeType.AT_PYTHON.value: _build_at_python,
        NodeType.AT_SCRIPT.value: _build_at_script,
        NodeType.AT_STYLE.value: _build_at_style,
        NodeType.AT_EVENT.value: _build_at_event,
        NodeType.AT_REACT.value: _build_at_react,
    }
    #endregion

    def build_node(self, template: HTMLTemplate, parent: Optional[RenderNode] = None) -> Optional[RenderNode | list[RenderNode]]:
        if (node_name := template.attributes.get('data-node')) is not None:
            data_node = RenderNode(None, NullContextShot(), parent.session)
            data_node.context = parent.context
            if not self.ctx.data_nodes:
                self.ctx.data_nodes = {}
            self.ctx.data_nodes[node_name] = data_node
            parent = data_node
        node = self.NODE_BUILDERS[template.node_type.value](self, template, parent)
        return node

    #region Node updaters
    def _update_html_node(self, node: HTMLElement, recursive):
        # attributes, classes, styles and text evaluation
        node.attributes.refresh()
        if (v := node.attributes.get('bind:value')) is not None:
            node.value = self.ctx.locals[v]

        if isinstance(node.classes, DynamicClasses):
            node.classes.refresh()
        if isinstance(node.style, DynamicStyles):
            node.style.refresh()
        node.data.refresh()

        node.text = node.attributes.get('$')

        node.shot(node)
        return recursive

    def _update_context_node(self, node, recursive):
        for attr, value in node.attributes.refresh_items():
            node.set_quietly(attr, value)
        return recursive

    def _update_text_node(self, node, recursive):
        node.refresh()
        return False

    def _update_condition_node(self, node, recursive):
        state: int
        condition: Optional[Condition]
        for i, c in enumerate(node.conditions):
            if c.func():
                state = i
                condition = c
                break
        else:
            state = -1
            condition = None

        if node.state != state:
            if node.state >= 0:
                node.empty()
            node.state = state
            if state == -1:
                return False

            node.renderer._build_group(condition.template, node)

            return False
        return recursive

    def _update_loop_node(self, node: LoopNode, recursive):
        if not node.index_func:
            node.empty()
            empty = True
            iter = node.iterator()
            if iter:
                parentloop = self.ctx.locals.get('forloop')
                for_loop = ForLoopType(parentloop)
                self.ctx.locals['forloop'] = for_loop
                for i, value in enumerate(iter):
                    empty = False
                    self.ctx.locals[node.var_name] = value
                    for_loop.counter = i + 1
                    for_loop.counter0 = i
                    node.renderer._build_group(node.loop_template, node)
                if node.var_name in self.ctx.locals:
                    del self.ctx.locals[node.var_name]
                if parentloop:
                    self.ctx.locals['forloop'] = parentloop
                else:
                    del self.ctx.locals['forloop']
        else:
            empty = not node.index_map
            if empty:
                node.empty()
            iter = node.iterator()
            if iter:
                oldmap = node.index_map
                node.index_map = newmap = {}

                pos = 0
                parentloop = self.ctx.locals.get('forloop')
                for_loop = ForLoopType(parentloop)
                self.ctx.locals['forloop'] = for_loop
                for i, value in enumerate(iter):
                    self.ctx.locals[node.var_name] = value
                    for_loop.counter = i + 1
                    for_loop.counter0 = i
                    index = node.index_func()
                    for_loop.index = index
                    if index in oldmap:
                        for sub in oldmap[index]:  # type: RenderNode
                            sub.move(pos)
                            sub.rebind()
                            pos += 1
                        newmap[index] = oldmap[index]
                        del oldmap[index]
                    else:
                        newmap[index] = []
                        for temp_child in node.loop_template:
                            sub = node.renderer.build_node(temp_child, node)
                            sub.move(pos)
                            newmap[index].append(sub)
                            pos += 1
                if node.var_name in self.ctx.locals:
                    del self.ctx.locals[node.var_name]
                if parentloop:
                    self.ctx.locals['forloop'] = parentloop
                else:
                    del self.ctx.locals['forloop']
                for lst in oldmap.values():
                    for sub in lst:
                        sub.remove()
                    lst.clear()
                empty = not node.index_map

        if empty and node.else_template:
            for temp_child in node.else_template.children:
                node.renderer.build_node(temp_child, node)

        return False

    def _update_set_node(self, node: SetNode, recursive):
        node.variables.refresh()
        if node.scoped:
            self.ctx.scope.update(node.variables)
        else:
            self.ctx.locals.update(node.variables)
        if node.self_clear:
            node.empty()
            node.renderer._build_group(node.template, node)
            #del self.ctx.locals[node.var_name]
            return False
        else:
            return recursive

    NODE_UPDATERS: dict[str, Callable[[Self, RenderNode, bool], bool]] = {
        'HTMLElement': _update_html_node,
        'NSElement': _update_html_node,
        'Context': _update_context_node,
        'TextNode': _update_text_node,
        'ConditionNode': _update_condition_node,
        'LoopNode': _update_loop_node,
        'SetNode': _update_set_node,
        'ReactNode': lambda *args: True,
    }
    #endregion

    def update(self, node: RenderNode, recursive: bool = False):
        if self.NODE_UPDATERS[typename(node)](self, node, recursive):
            self.update_children(node)
