from __future__ import annotations

import typing
from contextlib import contextmanager

from compiler import compile_context_code
from core.common import DynamicString, DynamicStyles, DynamicClasses, UniqueNode, typename, ADict
from core.components.htmlnode import HTMLTemplate
from core.components.loader import collect_template
from core.session import Session, run_safe

if typing.TYPE_CHECKING:
    from typing import *
    from core.components.context import AnyNode, Context, HTMLElement, Condition, \
        TextNode, Slot

__all__ = ['RenderNode', 'DefaultRenderer', 'ContextShot']


class RenderNode(UniqueNode):
    __slots__ = ['context', 'shot', 'session', 'render_this', 'name', 'scope', '_rebind']

    def __init__(self, parent: Optional[RenderNode], render_this: bool = False, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        super().__init__(parent)
        self.shot: 'ContextShot' = shot or parent.shot
        self.session: Session = session or parent.session
        self.scope: ADict[str, Any] = ADict() if not parent else parent.scope
        self.render_this: bool = render_this
        if render_this:
            self.shot(self)
        if typename(self) == 'Context':
            self.context = self
        else:
            self.context = parent.context
        self.name = ''
        self._rebind = False

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

    def select(self, predicate: Union[Iterable[str], Callable[[AnyNode], bool]]) -> Generator[AnyNode]:
        if isinstance(predicate, str):
            yield from super().select(lambda node: node.tag_name == predicate)
        elif isinstance(predicate, typing.Iterable):
            yield from super().select(lambda node: node.tag_name in predicate)
        else:
            yield from super().select(predicate)


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
            return self.build_func(self.strip_quotes(source).strip('{}'), node)()
        else:
            return self.strip_quotes(source)

    def process_special_attribute(self, attr: str, value: str, node: Optional[HTMLElement] = None) -> bool:
        if attr.startswith('ref:'):
            name = attr.split(':')[1].strip()
            self.ctx.refs[name] = node
            node.name = name
            return True
        elif attr.startswith('local:'):
            name = attr.split(':')[1].strip()
            #node.context.locals[name] = self.build_func(self.strip_quotes(value).strip('{}'), node)
            node.context.locals[name] = self.trace_eval(self.ctx, self.strip_quotes(value), node)
            return True
        elif attr == 'scope':
            node.scope = ADict(node.scope)
            return True
        elif attr.startswith('scope:'):
            name = attr.split(':')[1].strip()
            node.scope[name] = self.trace_eval(self.ctx, self.strip_quotes(value), node)
            return True
        elif attr == 'style':
            if node.style:
                self.ctx.session.error(f'Style already set before {attr}={value}')
                return True
            if '{' in value:
                node.style = self.build_string(value, node)
            else:
                node.style = DynamicStyles(self.strip_quotes(value))
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
        elif attr.startswith('css:'):
            if type(node.style) != DynamicStyles:
                self.ctx.session.error(f'Can not combine dynamic classes with expressions {attr}={value}')
                return True
            ctx = self.ctx
            attr = attr.split(':')[1].strip()
            if value is None:
                node.style[attr] = DynamicString(lambda: ctx.locals.get(attr))
            elif '{' in value:
                node.style[attr] = DynamicString(self.build_func('f'+value, node))
            else:
                value = self.strip_quotes(value)
                node.style[attr] = value #DynamicString(lambda: ctx.locals.get(value))
            return True
        elif attr == 'on:render':
            return True
        elif attr == 'bind:value':
            if value is None:
                value = 'value'
            else:
                value = self.strip_quotes(value)
            ctx = self.ctx
            node.attributes[attr] = value
            node.attributes.value = DynamicString(lambda: ctx.locals.get(value))
            return True
        elif attr.startswith('not:'):
            attr = attr.split(':')[1].strip()
            node.locals[attr] = False
            return True
        elif attr == 'set:focus':
            node._set_focus = True
            return True
        elif attr.startswith('data:'):
            attr = attr.split(':')[1].strip()
            node.data[attr] = self.eval_string(self.strip_quotes(value), node)
            return True
        return False

    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode] = None) -> Optional[AnyNode]:
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
                sides = template.macro.split('#')
                chunks = sides[0].split(' in ')
                node.var_name = chunks[0].strip()
                node.iterator = self.build_func(chunks[1], node)
                if len(sides) > 1:
                    node.index_func = self.build_func(sides[1], node)

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
                        data = self.eval_string(value, node) if value else True
                        node.locals[attr] = data

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
                        data = self.eval_string(value, node) if value else True
                        node.locals[attr] = data

            node.render.build()

        elif template.tag_name == 'slot':
            slot: Slot = parent.context.slot
            slot_template = None
            if slot:
                name = template.attributes.get('name')
                if name:
                    name = self.build_string(name, parent)
                    slot_template = slot[name]
                else:
                    slot_template = slot.template

            if not slot_template:
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
                for child in slot_template.children:
                    self.build_node(child, parent)
                self.ctx.ns_type = save_ns
                parent.context = save_ctx
                self.ctx = save_ctx

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
                    node.attributes[k] = ','.join(f'.{self.ctx.template.name} {s}' for s in self.strip_quotes(v).split(','))
                else:
                    node.attributes[k] = self.build_string(v, node)
            self.ctx.render_base = True

        elif template.tag_name == 'scope':
            scope = parent.scope
            for k, v in template.attributes.items():
                scope[k] = self.eval_string(v, parent)

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

    def rebind(self, node):
        if node.render_this or typename(node) == 'Context' and node.render_base:
            self.ctx.shot(node)
        else:
            for child in node.children:
                self.rebind(child)

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
            elif type(node.style) == DynamicStyles:
                for k, v in node.style.items():
                    if type(v) == DynamicString:
                        node.style[k] = v()
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
            if not node.index_func:
                node.empty()
                empty = True
                iter = node.iterator()
                if iter:
                    for value in iter:
                        empty = False
                        self.ctx.locals[node.var_name] = value
                        for temp_child in node.template.children:
                            self.build_node(temp_child, node)
                    del self.ctx.locals[node.var_name]
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
                        for value in iter:
                            self.ctx.locals[node.var_name] = value
                            index = node.index_func()
                            if index in oldmap:
                                for sub in oldmap[index]:
                                    node.move(sub.index(), pos)
                                    self.rebind(sub)
                                    pos += 1
                                newmap[index] = oldmap[index]
                                del oldmap[index]
                                continue
                            newmap[index] = []
                            for temp_child in node.template.children:
                                sub = self.build_node(temp_child, node)
                                node.move(len(node.children)-1, pos)
                                newmap[index].append(sub)
                                pos += 1
                        del self.ctx.locals[node.var_name]
                        for sub in oldmap.values():
                            sub.remove()
                        empty = not node.index_map

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
    __slots__ = ['updated', 'deleted', '_frozen', '_freeze_list', '_rebind']

    def __init__(self):
        self.updated: List[AnyNode] = list()
        self.deleted: Set[int] = set()
        self._frozen = False
        self._rebind = False
        self._freeze_list = None

    def reset(self):
        self.updated.clear()
        self.deleted.clear()

    @contextmanager
    def freeze(self):
        self._frozen = True
        self._freeze_list = []
        yield
        for node in self._freeze_list:
            node.parent.remove(node)
        self._freeze_list = None
        self._frozen = False

    @contextmanager
    def rebind(self):
        self._rebind = True
        yield
        self._rebind = False

    def __call__(self, node):
        if not self._frozen:
            if self._rebind:
                node._rebind = True
            self.updated.append(node)
        else:
            self._freeze_list.append(node)

    def __add__(self, other):
        self.__call__(other)
        return self

    def __sub__(self, other):
        self.deleted.add(other.oid)
        return self

    @property
    def rendered(self) -> List[RenderNode]:
        from core.components.context import Context
        return [node for node in self.updated if type(node) != Context or node.render_base]
