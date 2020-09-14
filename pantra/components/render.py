from __future__ import annotations

import typing
import traceback
from contextlib import contextmanager
from types import CodeType

from pantra.common import DynamicString, DynamicStyles, DynamicClasses, UniqueNode, typename, ADict
from pantra.components.loader import collect_template, HTMLTemplate
from pantra.compiler import compile_context_code, ContextInitFailed
from pantra.session import Session, run_safe

if typing.TYPE_CHECKING:
    from typing import *
    from pantra.components.context import AnyNode, Context, HTMLElement, Condition, \
        TextNode, Slot
    StrOrCode = Union[str, CodeType]

__all__ = ['RenderNode', 'DefaultRenderer', 'ContextShot']


class RenderNode(UniqueNode):
    __slots__ = ['context', 'shot', 'session', 'render_this', 'name', 'scope', '_rebind']

    def __init__(self: AnyNode, parent: Optional[AnyNode], render_this: bool = False, shot: Optional[ContextShot] = None, session: Optional[Session] = None):
        super().__init__(parent)
        self.shot: 'ContextShot' = shot or parent.shot
        self.session: Session = session or parent.session
        self.scope: ADict[str, Any] = ADict() if not parent else parent.scope
        self.render_this: bool = render_this
        if render_this:
            self.shot(self)
        if typename(self) == 'Context':
            self.context: Context = self
        else:
            self.context = parent.context
        self.name = ''
        self._rebind = False

    @property
    def parent(self) -> Optional[AnyNode]: return None
    del parent

    @property
    def children(self) -> List[AnyNode]: return []
    del children

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

    def update(self, with_attrs: bool = False):
        if with_attrs:
            self.context.render.update(self)
        else:
            self.shot(self)

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

    def select(self, predicate: Union[str, Iterable[str], Callable[[AnyNode], bool]], depth: int = 0) -> Generator[AnyNode]:
        if isinstance(predicate, str):
            yield from super().select(lambda node: str(node) == predicate, depth)
        elif isinstance(predicate, typing.Iterable):
            yield from super().select(lambda node: str(node) in predicate, depth)
        else:
            yield from super().select(predicate, depth)

    def set_scope(self, data: Union[Dict, str], value: Any = None):
        if isinstance(data, str):
            data = {data: value}
        self.scope = ADict(self.scope) | data


class DefaultRenderer:
    __slots__ = ['ctx']

    def __init__(self, ctx: Context):
        self.ctx: Context = ctx

    def __call__(self, template: Union[str, HTMLTemplate], parent: AnyNode = None, locals: Dict = None, build: bool = True):
        return self.render(template, parent, locals, build)

    def build(self):
        try:
            self.build_node(self.ctx.template, self.ctx)
        except ContextInitFailed:
            self.ctx.remove()

    @staticmethod
    def trace_eval(ctx: Context, text: StrOrCode, node: AnyNode):
        try:
            return eval(text, {'ctx': ctx, 'this': node}, ctx.locals)
        except:
            ctx.session.error(f'{ctx.template.name}/{node}: evaluation error: {traceback.format_exc(-3)}')
            return None

    def build_func(self, text: StrOrCode, node: AnyNode) -> Callable[[], Any]:
        # return lambda: eval(text, {'ctx': self.ctx, 'this': node}, self.ctx.locals)
        ctx = self.ctx  # save ctx to lambda instead of self, as ctx could be temporarily changed by slot
        return lambda: self.trace_eval(ctx, text, node)

    def translate(self, s):
        if s.startswith('\\'):
            return s[1:]
        if s.startswith('#'):
            return self.ctx.session.gettext(s[1:])
        return s

    def build_string(self, source: StrOrCode, node: AnyNode) -> Optional[Union[str, DynamicString]]:
        if source is None:
            return None
        if typename(source) == 'code':
            return DynamicString(self.build_func(source, node))
        else:
            return self.translate(source)

    def eval_string(self, source: StrOrCode, node: AnyNode) -> Any:
        if source is None:
            return None

        if typename(source) == 'code':
            return self.trace_eval(self.ctx, source, node)
        if source.startswith('@'):
            if ' ' in source:
                res = []
                for var in source[1:].split(' '):
                    res.append(self.ctx[var])
                return res
            return self.ctx[source[1:]]
        return self.translate(source)

    def build_bool(self, source: StrOrCode, node: AnyNode) -> Union[str, DynamicString]:
        if not source:
            return 'True'
        if typename(source) == 'code':
            return DynamicString(self.build_func(source, node))
        else:
            ctx = self.ctx
            return DynamicString(lambda: ctx.locals.get(source) or '')

    def process_special_attribute(self, attr: str, value: StrOrCode, node: Union[HTMLElement, Context]) -> bool:
        # common attributes
        if ':' in attr:
            if attr.startswith('ref:'):
                name = attr.split(':')[1].strip()
                self.ctx.refs[name] = node
                node.name = name
                return True
            if attr.startswith('cref:'):
                if typename(node) != 'Context':
                    self.ctx.session.error('Use cref: with components only')
                    return True
                name = attr.split(':')[1].strip()
                self.ctx.refs[name] = node.locals
                return True
            """
            if attr.startswith('local:'):
                name = attr.split(':')[1].strip()
                # node.context.locals[name] = self.build_func(self.strip_quotes(value).strip('{}'), node)
                node.context.locals[name] = self.trace_eval(self.ctx, value, node)
                return True
            """
            if attr.startswith('scope:'):
                name = attr.split(':')[1].strip()
                node.scope[name] = self.trace_eval(self.ctx, value, node)
                return True
            if attr == 'on:render':
                return True
            if attr == 'on:init':
                run_safe(self.ctx.session, lambda: self.ctx[value](node))
                return True
        else:
            if attr == 'scope':
                node.scope = ADict(node.scope)
                return True

        # HTMLElement's only
        if typename(node) == 'HTMLElement':
            if ':' in attr:
                if attr.startswith('class:'):
                    cls = attr.split(':')[1].strip()
                    ctx = self.ctx
                    if value is None:
                        func = lambda: ctx.locals[cls]
                    else:
                        if typename(value) == 'code':
                            func = self.build_func(value, node)
                        else:
                            func = lambda: ctx.locals[value]
                    node.con_classes.append((func, cls))
                    return True
                if attr.startswith('css:'):
                    if type(node.style) != DynamicStyles:
                        self.ctx.session.error(f'Can not combine dynamic style with expressions {attr}={value}')
                        return True
                    ctx = self.ctx
                    attr = attr.split(':')[1].strip()
                    if value is None:
                        node.style[attr] = DynamicString(lambda: ctx.locals.get(attr))
                    else:
                        node.style[attr] = self.build_string(value, node)
                    return True
                if attr == 'bind:value':
                    if value is None:
                        value = 'value'
                    node.attributes[attr] = value
                    # ctx = self.ctx
                    # node.value = lambda: ctx.locals.get(value)
                    self.ctx.locals._record(value)
                    return True
                if attr.startswith('set:'):
                    attr = attr.split(':')[1].strip()
                    if value is None:
                        value = attr
                    value = self.build_bool(value, node)
                    if attr == 'focus':
                        node._set_focus = bool(value)
                    else:
                        node.attributes[attr] = value
                    return True
                if attr.startswith('data:'):
                    attr = attr.split(':')[1].strip()
                    node.data[attr] = self.eval_string(value, node)
                    return True
            else:
                if attr == 'style':
                    if node.style:
                        self.ctx.session.error(f'Styles already set before {attr}={value}')
                        return True
                    node.style = self.build_string(value, node)
                    return True
                if attr == 'class':
                    if typename(value) == 'code':
                        node.classes = self.build_string(value, node)
                    else:
                        node.classes = DynamicClasses(value)
                    return True
                if attr == 'type':
                    node.value_type = self.eval_string(value, node)
                    return True
        else:
            # Context's only
            if attr.startswith('not:'):
                attr = attr.split(':')[1].strip()
                node.locals[attr] = False
                return True
            if attr == 'consume':
                if value is not None:
                    if value == '*':
                        node.locals |= node.parent.context.locals
                    else:
                        for at in value.split(','):
                            at = at.strip()
                            if at in node.parent.context.locals:
                                node[at] = node.parent[at]
                return True

        return False

    def build_node(self, template: HTMLTemplate, parent: Optional[AnyNode] = None) -> Optional[AnyNode]:
        import pantra.components.context as c
        node: Optional[AnyNode] = None

        tag_name = template.tag_name
        if tag_name[0].islower():
            # reconstruct HTML element

            node = c.HTMLElement(tag_name, parent=parent)

            with self.ctx.record_reactions(node):
                # evaluate attributes
                for attr, value in template.attributes.items():
                    if not self.process_special_attribute(attr, value, node):
                        node.attributes[attr] = self.build_string(value, node)

                node.con_classes()

                # evaluate body
                # element.text = self.build_string(template.text)

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

            for child in template.children:
                self.build_node(child, node)

            if 'on:render' in template.attributes:
                value = template.attributes['on:render']
                run_safe(self.ctx.session, lambda: self.ctx[value](node))

        elif tag_name[0].isupper():
            node_template = collect_template(self.ctx.session, tag_name)
            if not node_template: return None
            node = c.Context(node_template, parent)
            if 'consume' in template.attributes and template.attributes['consume'] is None:
                node.locals = parent.context.locals
                node.refs = parent.context.refs

            # attach slots
            if template.children:
                node.slot = c.Slot(self.ctx, template)

            # evaluate attributes
            with self.ctx.record_reactions(node):
                for attr, value in template.attributes.items():
                    if not self.process_special_attribute(attr, value, node):
                        data = self.eval_string(value, node) if value is not None else True
                        node.locals[attr] = data

            try:
                node.render.build()
            except ContextInitFailed:
                node.remove()
                return None

            if 'on:render' in template.attributes:
                value = template.attributes['on:render']
                run_safe(self.ctx.session, lambda: self.ctx[value](node))

        elif tag_name[0] == '$':
            node = self.ctx
            node.context = node

            for child in template.children:
                self.build_node(child, node)

        elif tag_name[0] == '#':
            if tag_name == '#if':
                node = c.ConditionNode(parent)
                for child_template in template.children:  # type: HTMLTemplate
                    if child_template.tag_name != '#else':
                        item = c.Condition(self.build_func(child_template.macro, node), child_template)
                    else:
                        item = c.Condition((lambda: True), child_template)
                    node.conditions.append(item)
                self.update(node, record_reactions=True)

            elif tag_name == '#for':
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

            elif tag_name == '#set':
                node: c.SetNode = c.SetNode(parent, template)
                chunks = template.macro.split(':=')
                if len(chunks) == 2:
                    node.var_name = chunks[0].strip()
                    node.expr = self.build_func(chunks[1], node)
                    self.update(node)

        elif tag_name[0] == '@':
            if tag_name == '@component':
                if 'render' in template.attributes:
                    renderer = template.attributes['render']
                    if renderer not in self.ctx.locals:
                        self.ctx.session.error(f'component renderer {renderer} not found')
                        return None
                    self.ctx.locals[renderer](parent)
                else:
                    for child in template.children:
                        self.build_node(child, parent)

            elif tag_name == '@slot':
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

            elif tag_name == '@python':
                if not self.ctx._executed:
                    self.ctx._executed = True
                    compile_context_code(self.ctx, template)

            elif tag_name == '@style':
                # styles collected elsewhere
                if 'global' not in template.attributes:
                    self.ctx._restyle = True

            elif tag_name == '@event':
                node = c.EventNode(parent)
                for k, v in template.attributes.items():
                    if k == 'selector':
                        if 'global' in template.attributes:
                            node.attributes[k] = v
                        else:
                            node.attributes[k] = ','.join(f'.{self.ctx.template.name} {s}' for s in v.split(','))
                            self.ctx._restyle = True
                    else:
                        node.attributes[k] = self.build_string(v, node)

            elif tag_name == '@scope':
                scope = parent.scope
                for k, v in template.attributes.items():
                    scope[k] = self.eval_string(v, parent)

            elif tag_name == '@text':
                text = template.text
                if text and text.startswith('#'):
                    text = self.ctx.session.gettext(text[1:])
                node = c.TextNode(parent, text)

            elif tag_name == '@macro':
                node = c.TextNode(parent, DynamicString(self.build_func(template.macro, node)))

            elif tag_name == '@react':
                var_name = template.attributes.get('to')
                action = template.attributes.get('action')
                if not var_name or not action:
                    self.ctx.session.error('<react> tag must have attributes `to` and `action`')
                    return None
                node = c.ReactNode(parent, var_name, action)
                # take in account consumed contexts
                self.ctx.locals._ctx.react_vars[var_name].add(node)

        return node

    def rebind(self, node: AnyNode):
        if node.render_this:
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

        elif typename(node) == 'Context':
            '''
            if node.children:
                node.empty()
            self.build_node(node.template, node)
            return  # prevent repeated updates
            # but now it only updates via update_tree
            '''

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
                    parentloop = self.ctx.locals.get('forloop')
                    self.ctx.locals['forloop'] = ADict(parent=parentloop)
                    for i, value in enumerate(iter):
                        empty = False
                        self.ctx.locals[node.var_name] = value
                        self.ctx.locals['forloop'].counter = i + 1
                        self.ctx.locals['forloop'].counter0 = i
                        for temp_child in node.template.children:
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
                                continue
                            newmap[index] = []
                            for temp_child in node.template.children:
                                sub = self.build_node(temp_child, node)
                                node.move(len(node.children)-1, pos)
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

            return  # prevent repeated updates

        elif typename(node) == 'SetNode':
            node.empty()
            self.ctx.locals[node.var_name] = node.expr()
            for child in node.template.children:
                self.build_node(child, node)
            del self.ctx.locals[node.var_name]

        '''
        elif typename(node) == 'ReactNode':
            if not recursive:
                process_click_referred(self.ctx.session, node, node.action)
            return'''

        if recursive:
            self.update_children(node)

    def render(self, template: Union[str, HTMLTemplate], parent: AnyNode = None, locals: Dict = None, build: bool = True):
        from pantra.components.context import Context
        if not parent:
            parent = self.ctx
        c = Context(template, parent, locals=locals)
        if build:
            c.render.build()
        return c


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
