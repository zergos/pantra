from __future__ import annotations

import typing

from compiler import compile_context_code
from core.common import DynamicString, DynamicStyles, DynamicClasses, UniqueNode, typename
from core.components.htmlnode import HTMLTemplate
from core.components.loader import collect_template
from core.session import Session, run_safe

if typing.TYPE_CHECKING:
    from typing import *
    from core.components.context import AnyNode, Context, HTMLElement, Condition, \
        TextNode, Slot

__all__ = ['RenderNode', 'DefaultRenderer', 'ContextShot']


class RenderNode(UniqueNode):
    __slots__ = ['context', 'shot', 'session', 'render_this']

    def __init__(self, parent: Optional[RenderNode], render_this: bool = False, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        super().__init__(parent)
        self.shot: 'ContextShot' = shot or parent.shot
        self.session: Session = session or parent.session
        self.render_this: bool = render_this
        if render_this:
            self.shot(self)
        if typename(self) == 'Context':
            self.context = self
        else:
            self.context = parent.context

    def _cleanup_node(self, node):
        if node in self.context.react_nodes:
            self.context.react_nodes.remove(node)
            for v in self.context.react_vars.values():
                if node in v:
                    v.remove(node)
        if node in self.context.refs.values():
            k = next(k for k, v in self.context.refs.items() if v == node)
            del self.context.refs[k]

    def empty(self):
        for child in self.children:  # type: RenderNode
            self.shot -= child
            self._cleanup_node(child)
            child.empty()
        self.children.clear()

    def remove(self, node=None):
        if node:
            node.parent.context._cleanup_node(node)
            super().remove(node)
        else:
            self.empty()
            self.shot -= self
            self._cleanup_node(self)
            if self.parent:
                self.parent.remove(self)

    def update(self):
        self.context.render.update(self)

    def update_tree(self):
        self.context.render.update(self, True)

    def _clone(self, new_parent: AnyNode) -> Optional[HTMLElement, TextNode]:
        return None

    def clone(self, new_parent: Optional[AnyNode] = None) -> Optional[HTMLElement, TextNode]:
        if new_parent is None:
            new_parent = self.context

        clone: Optional[AnyNode] = self._clone(new_parent)
        if clone:
            for child in self.children:
                sub = child.clone(clone)
                if sub:
                    clone.append(sub)
        return clone


class DefaultRenderer:
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

    def __call__(self, node: AnyNode, content: Union[str, AnyNode]):
        self.render(node, content)

    def build(self):
        self.build_node(self.ctx.template, self.ctx)

    @staticmethod
    def trace_eval(ctx: Context, text: str, node: AnyNode):
        try:
            return eval(text, {'ctx': ctx, 'this': node}, ctx.locals)
        except Exception as e:
            ctx.session.error(f'{ctx.template.name}/{node}: evaluation error: {e}')
            return None

    def build_func(self, text: str, node: AnyNode) -> Callable[[], Any]:
        # return lambda: eval(text, {'ctx': self.ctx, 'this': node}, self.ctx.locals)
        ctx = self.ctx  # save ctx to lambda instead of self, as ctx could be temporarily changed by slot
        return lambda: self.trace_eval(ctx, text, node)

    @staticmethod
    def strip_quotes(s):
        return s.strip('" ''')

    def build_string(self, source: str, node: AnyNode) -> Optional[Union[str, DynamicString]]:
        if not source:
            return None

        if '{' in source:
            return DynamicString(self.build_func('f'+source, node))
        else:
            return self.strip_quotes(source)

    def eval_string(self, source: str, node: AnyNode) -> Any:
        if not source:
            return None

        if '{' in source:
            return self.build_func(self.strip_quotes(source), node)()
        else:
            return self.strip_quotes(source)

    def process_special_attribute(self, attr: str, value: str, node: Optional[HTMLElement] = None) -> bool:
        if attr.startswith('ref:'):
            name = attr.split(':')[1].strip()
            self.ctx.refs[name] = node
            return True
        elif attr.startswith('local:'):
            name = attr.split(':')[1].strip()
            node.context.locals[name] = self.eval_string(value, node)
            return True
        elif attr.startswith('class:'):
            cls = attr.split(':')[1].strip()
            ctx = self.ctx
            if value is None:
                func = lambda: ctx.locals[cls]
            else:
                value = self.strip_quotes(value)
                if '{' in value:
                    func = self.build_func(value.strip('{}'), node)
                else:
                    func = lambda: ctx.locals[value]
            node.con_classes.append((func, cls))
            return True
        elif attr == 'on:render':
            return True
        elif attr == 'bind:value':
            if value is None:
                value = 'value'
            value = self.strip_quotes(value)
            ctx = self.ctx
            node.attributes.value = DynamicString(lambda: ctx.locals.get(value))
            return False
        elif attr == 'style':
            if '{' in value:
                node.style = self.build_string(value, node)
            else:
                node.style = DynamicStyles(self.strip_quotes(value))
            return True
        return False

    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode]) -> Optional[AnyNode]:
        import core.components.context as c
        node: Optional[AnyNode] = None
        if template.tag_name[0] == '#':
            if template.tag_name == '#if':
                node = c.ConditionNode(parent)
                for child_template in template.children:  # type: HTMLTemplate
                    if child_template.tag_name != '#else':
                        item = c.Condition(self.build_func(child_template.macro, node), child_template)
                    else:
                        item = c.Condition((lambda: True), child_template)
                    node.conditions.append(item)
                self.update(node, record_reactions=True)

            elif template.tag_name == '#for':
                node: c.LoopNode = c.LoopNode(parent, template.children[0])
                chunks = template.macro.split(' in ')
                node.var_name = chunks[0].strip()
                node.iterator = self.build_func(chunks[1], node)

                if len(template.children) > 1:
                    node.else_template = template.children[1]
                self.update(node)

        elif template.tag_name[0].isupper():
            node_template = collect_template(self.ctx.session, template.tag_name)
            if not node_template: return None
            node = c.Context(node_template, parent)

            # attach slots
            if template.children:
                node.slot = c.Slot(self.ctx, template)

            # evaluate attributes
            with self.ctx.record_reactions(node):
                for attr, value in template.attributes.items():
                    if not self.process_special_attribute(attr, value, node):
                        node.locals[attr] = self.build_string(value, node) if value else True

            node.render.build()

            if 'on:render' in template.attributes:
                value = self.strip_quotes(template.attributes['on:render'])
                run_safe(self.ctx.session, lambda: self.ctx[value](node))


        elif template.tag_name == 'reuse':
            node_template = collect_template(self.ctx.session, self.strip_quotes(template.attributes.template))
            if not node_template: return None

            node = parent
            node.template = node_template
            # evaluate attributes
            with self.ctx.record_reactions(node):
                for attr, value in template.attributes.items():
                    if attr == 'template':
                        continue
                    if not self.process_special_attribute(attr, value, node):
                        node.locals[attr] = self.build_string(value, node)

            node.render.build()

        elif template.tag_name == 'slot':
            slot: Slot = parent.context.slot
            slot_template = None
            if slot:
                name = template.attributes.get('name')
                if name:
                    name = self.build_string(name, parent)
                    for child in slot.template.children:
                        if child.tag_name == name:
                            slot_template = child
                            break
                else:
                    slot_template = slot.template

            if not slot_template:
                for child in template.children:
                    self.build_node(child, parent)
            else:
                # temporarily replace local context
                # I know it's dirty, but it eliminates the need to add param context to all builders
                current_ctx = self.ctx
                parent.context = slot.ctx
                self.ctx = slot.ctx
                for child in slot_template.children:
                    self.build_node(child, parent)
                parent.context = current_ctx
                self.ctx = current_ctx

        elif template.tag_name == 'python':
            if not self.ctx._executed:
                self.ctx._executed = True
                compile_context_code(self.ctx, template)

        elif template.tag_name == 'style':
            # styles collected elsewhere
            if 'global' not in template.attributes:
                self.ctx.render_base = True

        elif template.tag_name == 'event':
            node = c.EventNode(parent)
            for k, v in template.attributes.items():
                if k == 'selector':
                    node.attributes[k] = ','.join(f'.ctx-{self.ctx.template.name} {s}' for s in self.strip_quotes(v).split(','))
                else:
                    node.attributes[k] = self.build_string(v, node)
            self.ctx.render_base = True

        elif template.tag_name == '@text':
            node = c.TextNode(parent, self.strip_quotes(template.text))

        elif template.tag_name == '@macro':
            node = c.TextNode(parent, DynamicString(self.build_func(template.macro, node)))

        elif template.tag_name[0] == '$':
            node = self.ctx
            node.context = node

            for child in template.children:
                self.build_node(child, node)

        else:
            # reconstruct HTML element

            node = c.HTMLElement(template.tag_name, parent=parent)

            with self.ctx.record_reactions(node):
                # evaluate attributes
                for attr, value in template.attributes.items():
                    if not self.process_special_attribute(attr, value, node):
                        node.attributes[attr] = self.build_string(value, node)

                node.classes = self.build_string(template.classes, node)
                if node.classes is None:
                    node.classes = DynamicClasses()
                elif type(node.classes) == str:
                    node.classes = DynamicClasses(node.classes)
                node.con_classes()

                # evaluate body
                # element.text = self.build_string(template.text)

                # evaluate children
                if len(template.children) == 1:
                    if template.children[0].tag_name == '@text':
                        node.text = template.children[0].text
                        return node
                    elif template.children[0].tag_name == '@macro':
                        node.text = DynamicString(self.build_func(template.children[0].macro, node))
                        return node

            for child in template.children:
                self.build_node(child, node)

            if 'on:render' in template.attributes:
                value = self.strip_quotes(template.attributes['on:render'])
                run_safe(self.ctx.session, lambda: self.ctx[value](node))

        return node

    def update_children(self, node: AnyNode):
        for child in node.children:  # type: AnyNode
            if child.context == self.ctx:
                self.update(child, True)
            else:
                child.update_tree()

    def update(self, node: AnyNode, recursive: bool = False, record_reactions: bool = False):
        if typename(node) in ('HTMLElement', 'NSElement'):
            # attributes, classes and text evaluation
            for k, v in node.attributes.items():
                if type(v) == DynamicString:
                    node.attributes[k] = v()
            if type(node.classes) == DynamicString:
                node.classes = node.classes()
            else:
                if type(node.classes) == str:
                    node.classes = DynamicClasses(node.classes)
            node.con_classes()

            if type(node.style) == DynamicString:
                node.style = node.style()
            if type(node.text) == DynamicString:
                node.text = node.text()
            node.shot(node)

        elif typename(node) == 'Context':
            '''
            if node.children:
                node.empty()
            self.build_node(node.template, node)
            return  # prevent repeated updates
            '''
            node.shot(node)

        elif typename(node) == 'TextNode':
            if type(node.text) == DynamicString:
                node.text = node.text()
            node.shot(node)
            return  # no children ever

        elif typename(node) == 'ConditionNode':
            state: int = -1
            condition: Optional[Condition] = None
            if record_reactions:
                with self.ctx.record_reactions(node):
                    for i, c in enumerate(node.conditions):
                        if c.func() and state < 0:
                            state = i
                            condition = c
            else:
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
                    return

                for child in condition.template.children:
                    self.build_node(child, node)

                return  # prevent repeated updates

        elif typename(node) == 'LoopNode':
            node.empty()
            empty = True
            iter = node.iterator()
            if iter:
                for value in iter:
                    empty = False
                    self.ctx.locals[node.var_name] = value
                    for temp_child in node.template.children:
                        self.build_node(temp_child, node)
            if empty and node.else_template:
                for temp_child in node.else_template.children:
                    self.build_node(temp_child, node)

            return  # prevent repeated updates

        if recursive:
            self.update_children(node)

    def render(self, node: AnyNode, content: Union[str, AnyNode]):
        if type(content) == str:
            node.text = content
            self.ctx.shot(node)
        else:
            content.parent = node
            self.update_children(node)


class ContextShot:
    __slots__ = ['updated', 'deleted']

    def __init__(self):
        self.updated: List[AnyNode] = list()
        self.deleted: Set[int] = set()

    def reset(self):
        self.updated.clear()
        self.deleted.clear()

    def __call__(self, node):
        self.updated.append(node)

    def __add__(self, other):
        self.updated.append(other)
        return self

    def __sub__(self, other):
        self.deleted.add(other.oid)
        return self

    @property
    def rendered(self) -> List[RenderNode]:
        from core.components.context import Context
        return [node for node in self.updated if type(node) != Context or node.render_base]
