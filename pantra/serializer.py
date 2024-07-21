import typing
from datetime import date, time, datetime, timezone

from .contrib import bsdf_lite as bsdf
from .common import DynamicString
from .components.context import HTMLElement, TextNode, EventNode, NSElement, ScriptNode, AnyNode, ConditionNode, LoopNode

__all__ = ['serializer']


def get_parent_oid(node: AnyNode) -> typing.Optional[int]:
    parent = node.parent
    while parent and not parent.render_this:
        parent = parent.parent
    return parent and parent.oid


class HTMLElementSerializer(bsdf.Extension):
    name = 'h'

    def match(self, s, v):
        return isinstance(v, HTMLElement)

    def encode(self, s, v: typing.Union[HTMLElement, NSElement]):
        res = {
            'n': v.tag_name,
            'i': v.oid,
            'p': get_parent_oid(v),
            'a': v.attributes,
            'C': v.classes + v.con_classes.cache,
            's': str(v.style),
            'f': v._set_focus,
            'l': v.localize,
        }
        if isinstance(v.text, DynamicString) and v.text.html:
            res['T'] = v.text
        else:
            res['t'] = v.text
        if type(v) == NSElement:
            res['x'] = v.ns_type.value
        if v._rebind:
            res['#'] = True
            v._rebind = False
        if v.context._restyle:
            res['$'] = v.context.template.name
        if v.value_type:
            res['type'] = v.value_type
        value = getattr(v, '_value', None)
        if isinstance(value, HTMLElement):
            value = value.oid
        if value is not None:
            res['v'] = value
        return res


class TextSerializer(bsdf.Extension):
    name = 't'

    def match(self, s, v):
        return type(v) == TextNode

    def encode(self, s, v: TextNode):
        res = {'i': v.oid, 'p': get_parent_oid(v), 't': v.text}
        if v._rebind:
            res['#'] = True
            v._rebind = False
        return res


class StubElementSerializer(bsdf.Extension):
    name = 'd'

    def match(self, s, v):
        return isinstance(v, ConditionNode) or isinstance(v, LoopNode)

    def encode(self, s, v: typing.Union[HTMLElement, NSElement]):
        res = {
            'i': v.oid,
            'p': get_parent_oid(v),
        }
        if v.context._restyle:
            res['$'] = v.context.template.name
        return res


class EventSerializer(bsdf.Extension):
    name = 'e'

    def match(self, s, v):
        return type(v) == EventNode

    def encode(self, s, v):
        return {'ctx': v.context.template.name, 'a': v.attributes, 'oid': v.context.oid}


class DateSerializer(bsdf.Extension):
    name = 'D'

    def match(self, s, v):
        return type(v) == date

    def encode(self, s, v: date):
        return datetime(v.year, v.month, v.day, tzinfo=timezone.utc).timestamp()*1000

    def decode(self, s, v):
        if v < 0:
            return None
        if 32503680000000 > v > 864000000:
            return datetime.utcfromtimestamp(v//1000).date()
        if v < 864000000:
            return datetime.utcfromtimestamp(v//1000).time()
        return None


class TimeSerializer(bsdf.Extension):
    name = 'T'

    def match(self, s, v):
        return type(v) == time

    def encode(self, s, v: time):
        return datetime(1970, 1, 1, v.hour, v.minute, v.second, tzinfo=timezone.utc).timestamp()*1000


class ScriptSerializer(bsdf.Extension):
    name = 's'

    def match(self, s, v):
        return isinstance(v, ScriptNode)

    def encode(self, s, v: ScriptNode):
        return {'i': v.oid, 'u': v.uid, 'p': get_parent_oid(v), 'a': v.attributes, 't': v.text}


serializer = bsdf.BsdfLiteSerializer([HTMLElementSerializer, TextSerializer, EventSerializer,
                                      DateSerializer, TimeSerializer, ScriptSerializer, StubElementSerializer],
                                     compression='bz2')


