from __future__ import annotations

import typing
from .common import WebUnits, EmptyCaller, HTML, DynamicStyles, DynamicClasses
from .settings import config

AnyT = typing.TypeVar('AnyT')
Property = typing.Annotated[AnyT, 'Property']

if typing.TYPE_CHECKING:
    import logging
    from pantra.components.context import Context, HTMLElement, ActionType
    from pantra.components.render.render_node import RenderNode
    from pantra.session import Session
    from typing import *

    refs: dict[str, Context | HTMLElement | Any]
    ctx: Context
    session: Session
    logger: logging.Logger

    def _(message: str, *args, plural: str = None, n: int = None, ctx: str = None, many: bool = False): ...

    __all__ = ['Context', 'HTMLElement', 'Session', 'refs', 'ctx', 'session', '_', 'RenderNode',
               'Any', 'Callable', 'ClassVar', 'Generic', 'Optional', 'Tuple', 'Type', 'TypeVar', 'Union', 'AbstractSet',
               'ByteString', 'Container', 'ContextManager', 'Hashable', 'ItemsView', 'Iterable', 'Iterator', 'KeysView',
               'Mapping', 'MappingView', 'MutableMapping', 'MutableSequence', 'MutableSet', 'Sequence', 'Sized',
               'ValuesView', 'Awaitable', 'AsyncIterator', 'AsyncIterable', 'Coroutine', 'Collection', 'AsyncGenerator',
               'AsyncContextManager', 'Deque', 'Dict', 'DefaultDict', 'List', 'Set', 'FrozenSet', 'NamedTuple',
               'Generator', 'NewType', 'NoReturn', 'typing', 'WebUnits', 'logger', 'EmptyCaller', 'HTML',
               'config', 'ActionType', 'Property', 'DynamicStyles', 'DynamicClasses']
