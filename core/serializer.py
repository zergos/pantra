import bsdf
import typing

from core.components.context import Context, HTMLElement, ConditionNode, LoopNode, TextNode, EventNode, NSElement, \
    AnyNode

__all__ = ['serializer']


def get_parent_oid(node: AnyNode) -> typing.Optional[int]:
    parent = node.parent
    while parent and (type(parent) not in [HTMLElement, NSElement, TextNode, Context] or type(parent) == Context and not parent.render_base):
        parent = parent.parent
    return parent and parent.oid


class HTMLElementSerializer(bsdf.Extension):
    name = 'h'

    def match(self, s, v):
        return isinstance(v, HTMLElement)

    def encode(self, s, v: typing.Union[HTMLElement, NSElement]):
        res = {'n': v.tag_name, 'i': v.oid, 'p': get_parent_oid(v), 'a': v.attributes, 'C': v.classes + v.con_classes.cache, 't': v.text, 's': str(v.style), 'f': v._set_focus}
        if type(v) == NSElement:
            res['x'] = v.ns_type.value
        if v._rebind:
            res['#'] = True
        return res


class ContextSerializer(bsdf.Extension):
    name = 'c'

    def match(self, s, v):
        return type(v) == Context

    def encode(self, s, v: Context):
        res = {'n': v.template.name, 'i': v.oid, 'p': get_parent_oid(v)}
        if v._rebind:
            res['#'] = True
        return res


class ConditionSerializer(bsdf.Extension):
    name = 'i'

    def match(self, s, v):
        return type(v) == ConditionNode

    def encode(self, s, v: ConditionNode):
        return {'i': v.oid, 'p': get_parent_oid(v)}


class LoopSerializer(bsdf.Extension):
    name = 'l'

    def match(self, s, v):
        return type(v) == LoopNode

    def encode(self, s, v):
        return {'i': v.oid, 'p': get_parent_oid(v)}


class TextSerializer(bsdf.Extension):
    name = 't'

    def match(self, s, v):
        return type(v) == TextNode

    def encode(self, s, v: TextNode):
        res = {'i': v.oid, 'p': get_parent_oid(v), 't': v.text}
        if v._rebind:
            res['#'] = True
        return res


class EventSerializer(bsdf.Extension):
    name = 'e'

    def match(self, s, v):
        return type(v) == EventNode

    def encode(self, s, v):
        return {'ctx': v.context.template.name, 'a': v.attributes}


serializer = bsdf.BsdfSerializer([HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer, EventSerializer],
                                 compression='bz2')


