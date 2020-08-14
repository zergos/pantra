import contrib.bsdf_lite as bsdf
import typing
from datetime import date, time, datetime, timezone

from .components.context import HTMLElement, TextNode, EventNode, NSElement, AnyNode

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
        res = {'n': v.tag_name, 'i': v.oid, 'p': get_parent_oid(v), 'a': v.attributes, 'C': v.classes + v.con_classes.cache, 't': v.text, 's': str(v.style), 'f': v._set_focus}
        if type(v) == NSElement:
            res['x'] = v.ns_type.value
        if v._rebind:
            res['#'] = True
            v._rebind = False
        if v.context._restyle:
            res['$'] = v.context.template.name
        if v.value_type:
            res['type'] = v.value_type
        if getattr(v, '_value', None) is not None:
            res['v'] = v._value() if callable(v._value) else v._value
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
        return datetime.utcfromtimestamp(v//1000).date()


class TimeSerializer(bsdf.Extension):
    name = 'T'

    def match(self, s, v):
        return type(v) == time

    def encode(self, s, v: time):
        return datetime(1970, 1, 1, v.hour, v.minute, v.second, tzinfo=timezone.utc).timestamp()*1000


serializer = bsdf.BsdfLiteSerializer([HTMLElementSerializer, TextSerializer, EventSerializer,
                                      DateSerializer, TimeSerializer], compression='bz2')


