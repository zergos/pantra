from __future__ import annotations

import typing

from pantra.common import DynamicString, typename, DynamicStyles, DynamicClasses, ADict
from pantra.compiler import ContextInitFailed, compile_context_code
from pantra.session import run_safe
from ..template import AttrType, NodeType, collect_template, MacroCode
from ..context import HTMLElement, Context, AnyNode, Slot, ConditionNode, Condition, LoopNode, SetNode, ScriptNode, \
    EventNode, TextNode, ReactNode
from .renderer_base import RendererBase, StrOrCode
from .render_node import RE_JS_VARS

if typing.TYPE_CHECKING:
    from typing import Callable, Any, Self, Union, Optional
    from ..template import HTMLTemplate

class RendererHTML(RendererBase):
    #region Attribute processors
    @staticmethod
    def _return_false(*args):
        return False

    @staticmethod
    def _return_true(*args):
        return True

    def _process_attr_ref_name(self, attr_name, value, node):
        self.ctx.refs[attr_name] = node
        node.name = attr_name
        return True

    def _process_attr_cref_name(self, attr_name, value, node):
        if typename(node) != 'Context':
            self.ctx.session.error('Use cref: with components only')
            return True
        self.ctx.refs[attr_name] = node.locals
        return True

    def _process_attr_scope(self, attr_name, value, node):
        node.scope[attr_name] = self.trace_eval(self.ctx, value, node)
        return True

    def _process_attr_on_init(self, attr_name, value, node):
        run_safe(self.ctx, lambda: self.ctx[value](node), dont_refresh=True)
        return True

    def _process_attr_class_switch(self, attr_name, value, node):
        if value is None:
            value = attr_name
        func = self.build_func_or_local(value, node)
        node.con_classes.append((func, attr_name))
        return True

    def _process_attr_dynamic_style(self, attr_name, value, node):
        if type(node.style) != DynamicStyles:
            self.ctx.session.error(f'Can not combine dynamic style with expressions {attr_name}={value}')
            return True
        if value is None:
            node.style[attr_name] = DynamicString(self.build_func_or_local(attr_name, node, ''))
        else:
            node.style[attr_name] = DynamicString(self.build_string(value, node))
        return True

    def _process_attr_bind_value(self, attr_name, value, node):
        if value is None:
            value = 'value'
        node.attributes['bind:value'] = value
        if value in self.ctx.locals:
            node.value = self.ctx.locals[value]
        else:
            self.ctx.locals[value] = None
        with self.ctx.record_reactions(node):
            _ = self.ctx.locals[value]
        return True

    def _process_attr_dynamic_set(self, attr_name, value, node):
        if value is None:
            value = attr_name
        if isinstance(value, str) and value == "yes":
            value = lambda: True
        elif isinstance(value, str) and value == "no":
            value = lambda: False
        else:
            value = self.build_func_or_local(value, node, '')
        if attr_name == 'focus':
            node._set_focus = bool(value())
        elif attr_name == 'type':
            self._process_attr_type(None, value(), node)
        elif attr_name == 'localize':
            self._process_attr_localize(None, bool(value()), node)
        else:
            node.attributes[attr_name] = DynamicString(lambda: value() or '')
        return True

    def _process_attr_dynamic_set_ctx(self, attr_name, value, node):
        if value is None:
            value = True
        elif isinstance(value, str) and value == "yes":
            value = True
        elif isinstance(value, str) and value == "no":
            value = False
        else:
            value = self.eval_string(value, node)
        node.locals[attr_name] = value
        return True

    def _process_attr_data(self, attr_name, value, node):
        node.data[attr_name] = self.eval_string_i10n(value, node)
        return True

    def _process_attr_src_href(self, attr_name, value, node):
        node.attributes[attr_name] = self.ctx.static(attr_name, self.trace_eval(self.ctx, value, node) if type(
            value) is MacroCode else value)
        return True

    def _process_attr_style(self, attr_name, value, node):
        if node.style:
            self.ctx.session.error(f'Styles already set before {attr_name}={value}')
            return True
        node.style = self.build_string(value, node)
        return True

    def _process_attr_class(self, attr_name, value, node):
        if type(value) is MacroCode:
            node.classes = self.build_string(value, node)
        else:
            node.classes = DynamicClasses(value)
        return True

    def _process_attr_type(self, attr_name, value, node):
        node.value_type = self.eval_string(value, node)
        return True

    def _process_attr_value(self, attr_name, value, node):
        node.value = self.eval_string(value, node)
        return True

    def _process_attr_localize(self, attr_name, value, node):
        node.localize = self.eval_string(value, node)
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
                    if at in node.context.locals:
                        node[at] = node.context[at]
        return True

    PROCESS_HTML_ATTR: dict[int, Callable[[Self, str, Any, HTMLElement], bool]] = {
        AttrType.NO_SPECIAL.value: _return_false,
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

    PROCESS_CTX_ATTR: dict[int, Callable[[Self, str, Any, Context], bool]] = {
        AttrType.NO_SPECIAL.value: _return_false,
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

    def process_special_attribute_html(self, attr: tuple[AttrType, str | None], value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        return self.PROCESS_HTML_ATTR[attr[0].value](self, attr[1], value, node)

    def process_special_attribute_ctx(self, attr: tuple[AttrType, str | None], value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        return self.PROCESS_CTX_ATTR[attr[0].value](self, attr[1], value, node)

    #region Node builders
    def _build_html_tag(self, template, parent):
        if 'not:render' in template.attributes:
            # forget it
            return None

        node = HTMLElement(template.tag_name, parent=parent)

        with self.ctx.record_reactions(node, 'reactive' in template.attributes):
            # evaluate attributes
            for attr, value in template.attributes.items():
                if not self.process_special_attribute_html(template.attr_specs[attr], value, node):
                    node.attributes[attr] = self.build_string_i10n(value, node)

            node.con_classes()

            # evaluate body
            # element.text = self.build_string(template.text)

        if True:
            # evaluate children
            if len(template.children) == 1:
                if template.children[0].tag_name == '@text':
                    text = template.children[0].text
                    if text.startswith('#'):
                        text = self.ctx.session.gettext(text[1:])
                    node.text = text
                    return node
                elif template.children[0].tag_name == '@macro':
                    node.text = DynamicString(self.build_func(template.children[0].macro, node))
                    return node

        if 'node_processor' in self.ctx.locals:
            run_safe(node, lambda: self.ctx['node_processor'](node), dont_refresh=True)

        for child in template.children:
            self.build_node(child, node)

        if 'on:render' in template.attributes:
            value = template.attributes['on:render']
            run_safe(node, lambda: self.ctx[value](node), dont_refresh=True)

        return node

    def _build_template_tag(self, template, parent):
        node_template = collect_template(self.ctx.session, template.tag_name)
        if not node_template: return None
        node = Context(node_template, parent)
        node.source_attributes = template.attributes
        if 'consume' in template.attributes and template.attributes['consume'] is None:
            node.locals = node.context.locals
            node.refs = node.context.refs

        # attach slots
        if template.children:
            node.slot = Slot(self.ctx, template)

        # evaluate attributes
        # with self.ctx.record_reactions(node):
        if True:
            for attr, value in template.attributes.items():
                if not self.process_special_attribute_ctx(template.attr_specs[attr], value, node):
                    if isinstance(value, str) or isinstance(value, MacroCode):
                        data = self.eval_string_i10n(value, node)
                    elif value is None:
                        data = True
                    else:
                        data = value
                    node.locals[attr] = data

        if 'node_processor' in self.ctx.locals:
            run_safe(node, lambda: self.ctx['node_processor'](node), dont_refresh=True)

        try:
            node.renderer.build()
        except ContextInitFailed:
            node.remove()
            return None

        if 'on:render' in template.attributes:
            value = template.attributes['on:render']
            if value not in self.ctx.locals:
                raise ValueError(f'No renderer named `{value}` found in `{self.ctx.template.name}`')
            run_safe(node, lambda: self.ctx[value](node), dont_refresh=True)

        return node

    def _build_root_node(self, template, parent):
        node = self.ctx

        for child in template.children:
            self.build_node(child, node)

        if "on_render" in self.ctx.locals:
            run_safe(node, self.ctx["on_render"], dont_refresh=True)

        return node

    def _build_macro_if(self, template, parent):
        node = ConditionNode(parent, template)
        for child_template in template.children:  # type: HTMLTemplate
            if child_template.tag_name != '#else':
                item = Condition(self.build_func(child_template.macro, node), child_template)
            else:
                item = Condition((lambda: True), child_template)
            node.conditions.append(item)
        self.update(node)
        return node

    def _build_macro_for(self, template, parent):
        node: LoopNode = LoopNode(parent, template)
        loop_template = template[0]
        node.var_name = loop_template.text
        node.iterator = self.build_func(loop_template.macro[0], node)
        node.index_func = loop_template.macro[1].code and self.build_func(loop_template.macro[1], node)

        node.loop_template = loop_template
        if len(template.children) > 1:
            node.else_template = template[1]
        self.update(node)
        return node

    def _build_macro_set(self, template, parent):
        node: SetNode = SetNode(parent, template)
        node.var_name = template.text
        node.expr = self.build_func(template.macro, node)
        self.update(node)
        return node

    def _build_at_component(self, template, parent):
        if 'render' in template.attributes:
            renderer = template.attributes['render']
            if renderer not in self.ctx.locals:
                self.ctx.session.error(f'component renderer {renderer} not found')
                return None
            self.ctx.locals[renderer](parent)
        else:
            for child in template.children:
                self.build_node(child, parent)
        return self

    def _build_at_slot(self, template, parent):
        slot: Slot = parent.context.slot
        if slot:
            name = template.attributes.get('name')
            if name:
                name = self.build_string(name, parent)
                slot = slot[name]

        if not slot:
            for child in template.children:
                self.build_node(child, parent)
        else:
            # temporarily replace local context, but preserve ns_type
            # I know it's dirty, but it eliminates the need to add param context to all constructors
            save_ctx = self.ctx
            save_ns = slot.ctx.ns_type
            parent.context = slot.ctx
            self.ctx = slot.ctx
            self.ctx.ns_type = save_ctx.ns_type
            for child in slot.template.children:
                self.build_node(child, parent)
            self.ctx.ns_type = save_ns
            parent.context = save_ctx
            self.ctx = save_ctx
        return self

    def _build_at_python(self, template, parent):
        if not self.ctx._executed:
            self.ctx._executed = True
            compile_context_code(self.ctx, template)
        return self

    def _build_at_script(self, template, parent):
        def subst(matchobj) -> str:
            expr = matchobj.group(1)
            return self.ctx.locals.get(expr, str(self.trace_eval(self.ctx, expr, self.ctx)))

        text = RE_JS_VARS.sub(subst, template.text) if template.text else ""
        node = ScriptNode(parent, f'{self.ctx.template.name}_{template.index}', attributes=template.attributes.copy(),
                            text=text)
        return node

    def _build_at_style(self, template, parent):
        # styles collected elsewhere
        if 'global' not in template.attributes:
            self.ctx._restyle = True
        return self

    def _build_at_event(self, template, parent):
        node = EventNode(parent)
        for k, v in template.attributes.items():
            if k == 'selector':
                if 'global' in template.attributes:
                    node.attributes[k] = v
                else:
                    node.attributes[k] = ','.join(f'.{self.ctx.template.name} {s}' for s in v.split(','))
                    self.ctx._restyle = True
            else:
                node.attributes[k] = self.build_string(v, node)
        return node

    def _build_at_scope(self, template, parent):
        scope = {}
        for k, v in template.attributes.items():
            scope[k] = self.eval_string(v, parent)
        parent.set_scope(scope)
        return self

    def _build_at_text(self, template, parent):
        text = template.text
        if text and text.startswith('#'):
            text = self.ctx.session.gettext(text[1:])
        node = TextNode(parent, text)
        return node

    def _build_at_macro(self, template, parent):
        node = TextNode(parent, DynamicString(self.build_func(template.macro, parent)))
        return node

    def _build_at_react(self, template, parent):
        var_name = template.attributes.get('to')
        action = template.attributes.get('action')
        if not var_name or not action:
            self.ctx.session.error('<react> tag must have attributes `to` and `action`')
            return None
        node = ReactNode(parent, var_name, action)
        # take in account consumed contexts
        self.ctx.locals._ctx.react_vars[var_name].append(node)
        return node

    NODE_BUILDERS: dict[int, Callable[[Self, HTMLTemplate, AnyNode], AnyNode]] = {
        NodeType.HTML_TAG.value: _build_html_tag,
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
        NodeType.AT_SCOPE.value: _build_at_scope,
        NodeType.AT_TEXT.value: _build_at_text,
        NodeType.AT_MACRO.value: _build_at_macro,
        NodeType.AT_REACT.value: _build_at_react,
    }
    #endregion

    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode] = None) -> Optional[AnyNode]:
        return self.NODE_BUILDERS[template.node_type.value](self, template, parent)

    #region Node updaters
    def _update_html_node(self, node, recursive):
        # attributes, classes and text evaluation
        for k, v in node.attributes.items():
            if type(v) == DynamicString:
                node.attributes[k] = v()
            elif k == 'bind:value':
                node.value = self.ctx.locals[v]
        if type(node.classes) == DynamicString:
            node.classes = node.classes()
        node.con_classes()

        if type(node.style) == DynamicString:
            node.style = node.style()
        elif type(node.style) == DynamicStyles:
            for k, v in node.style.items():
                if type(v) == DynamicString:
                    node.style[k] = v()
        if type(node.text) == DynamicString:
            node.text = node.text()
        node.shot(node)
        return True

    def _update_context_node(self, node, recursive):
        if not recursive:
            for attr, value in node.source_attributes.items():
                if type(value) is MacroCode:
                    data = self.eval_string_i10n(value, node) if value is not None else True
                    node[attr] = data
            return False
        return True

    def _update_text_node(self, node, recursive):
        if type(node.text) is DynamicString:
            node.text = node.text()
        node.shot(node)
        return False

    def _update_condition_node(self, node, recursive):
        if node.render_this:
            node.shot(node)

        state: int = -1
        condition: Optional[Condition] = None
        for i, c in enumerate(node.conditions):
            if c.func():
                state = i
                condition = c
                break

        if node.state != state:
            if node.state >= 0:
                node.empty()
            node.state = state
            if state == -1:
                return False

            for child in condition.template.children:
                self.build_node(child, node)

            return False
        return True

    def _update_loop_node(self, node, recursive):
        if node.render_this:
            node.shot(node)

        if not node.index_func:
            node.empty()
            empty = True
            iter = node.iterator()
            if iter:
                parentloop = self.ctx.locals.get('forloop')
                self.ctx.locals['forloop'] = ADict(parent=parentloop)
                for i, value in enumerate(iter):
                    empty = False
                    self.ctx.locals[node.var_name] = value
                    self.ctx.locals['forloop'].counter = i + 1
                    self.ctx.locals['forloop'].counter0 = i
                    for temp_child in node.loop_template:
                        self.build_node(temp_child, node)
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
                with self.ctx.shot.rebind():
                    pos = 0
                    parentloop = self.ctx.locals.get('forloop')
                    self.ctx.locals['forloop'] = ADict(parentloop=parentloop)
                    for i, value in enumerate(iter):
                        self.ctx.locals[node.var_name] = value
                        self.ctx.locals['forloop'].counter = i + 1
                        self.ctx.locals['forloop'].counter0 = i
                        index = node.index_func()
                        self.ctx.locals['forloop'].index = index
                        if index in oldmap:
                            for sub in oldmap[index]:  # type: AnyNode
                                node.move(sub.index(), pos)
                                self.rebind(sub)
                                pos += 1
                            newmap[index] = oldmap[index]
                            del oldmap[index]
                        else:
                            newmap[index] = []
                            for temp_child in node.loop_template:
                                sub = self.build_node(temp_child, node)
                                node.move(len(node.children) - 1, pos)
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
                self.build_node(temp_child, node)

        return False

    def _update_set_node(self, node, recursive):
        node.empty()
        self.ctx.locals[node.var_name] = node.expr()
        for child in node.template.children:
            self.build_node(child, node)
        del self.ctx.locals[node.var_name]
        return False

    NODE_UPDATERS: dict[str, Callable[[Self, AnyNode, bool], bool]] = {
        'HTMLElement': _update_html_node,
        'NSElement': _update_html_node,
        'Context': _update_context_node,
        'TextNode': _update_text_node,
        'ConditionNode': _update_condition_node,
        'LoopNode': _update_loop_node,
        'SetNode': _update_set_node,
    }
    #endregion

    def update(self, node: AnyNode, recursive: bool = False):
        if self.NODE_UPDATERS[typename(node)](self, node, recursive) and recursive:
            self.update_children(node)
