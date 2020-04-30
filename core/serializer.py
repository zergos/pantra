from __future__ import annotations
import typing
import bsdf

from core.oid import gen_id
#if typing.TYPE_CHECKING:
from core.components.context import Context, HTMLElement, ConditionNode, LoopNode, TextNode, EventNode

class HTMLElementSerializer(bsdf.Extension):
    name = 'H'

    def match(self, s, v):
        return type(v) == HTMLElement

    def encode(self, s, v: HTMLElement):
        return {'n': v.tag_name, 'i': gen_id(v), 'c': v.children, 'a': v.attributes, 'C': v.classes, 't': v.text, 's': str(v.style)}


class ContextSerializer(bsdf.Extension):
    name = 'C'

    def match(self, s, v):
        return type(v) == Context

    def encode(self, s, v: Context):
        return {'n': v.template.name, 'i': gen_id(v), 'c': v.children}


class ConditionSerializer(bsdf.Extension):
    name = 'I'

    def match(self, s, v):
        return type(v) == ConditionNode

    def encode(self, s, v: ConditionNode):
        return {'i': gen_id(v), 'c': v.children}


class LoopSerializer(bsdf.Extension):
    name = 'L'

    def match(self, s, v):
        return type(v) == LoopNode

    def encode(self, s, v):
        return {'i': gen_id(v), 'c': v.children}


class TextSerializer(bsdf.Extension):
    name = 'T'

    def match(self, s, v):
        return type(v) == TextNode

    def encode(self, s, v: TextNode):
        return {'i': gen_id(v), 't': v.text}


class EventSerializer(bsdf.Extension):
    name = 'E'

    def match(self, s, v):
        return type(v) == EventNode

    def encode(self, s, v):
        return {'ctx': v.context.template.name, 'a': v.attributes}


serializer = bsdf.BsdfSerializer([HTMLElementSerializer, ContextSerializer, ConditionSerializer, LoopSerializer, TextSerializer, EventSerializer],
                                 compression='bz2')


class HTMLElementSerializer2(bsdf.Extension):
    name = 'h'

    def match(self, s, v):
        return type(v) == HTMLElement

    def encode(self, s, v: HTMLElement):
        return {'n': v.tag_name, 'i': gen_id(v), 'p': gen_id(v.parent), 'a': v.attributes, 'C': v.classes, 't': v.text, 's': str(v.style)}


class ContextSerializer2(bsdf.Extension):
    name = 'c'

    def match(self, s, v):
        return type(v) == Context

    def encode(self, s, v: Context):
        return {'n': v.template.name, 'i': gen_id(v), 'p': gen_id(v.parent)}


class ConditionSerializer2(bsdf.Extension):
    name = 'i'

    def match(self, s, v):
        return type(v) == ConditionNode

    def encode(self, s, v: ConditionNode):
        return {'i': gen_id(v), 'p': gen_id(v.parent)}


class LoopSerializer2(bsdf.Extension):
    name = 'l'

    def match(self, s, v):
        return type(v) == LoopNode

    def encode(self, s, v):
        return {'i': gen_id(v), 'p': gen_id(v.parent)}


class TextSerializer2(bsdf.Extension):
    name = 't'

    def match(self, s, v):
        return type(v) == TextNode

    def encode(self, s, v: TextNode):
        return {'i': gen_id(v), 'p': gen_id(v.parent), 't': v.text}


class EventSerializer2(bsdf.Extension):
    name = 'e'

    def match(self, s, v):
        return type(v) == EventNode

    def encode(self, s, v):
        return None


serializerU = bsdf.BsdfSerializer([HTMLElementSerializer2, ContextSerializer2, ConditionSerializer2, LoopSerializer2, TextSerializer2, EventSerializer2],
                                 compression='bz2')


