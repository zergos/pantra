from __future__ import annotations

import typing
from .common import WebUnits, EmptyCaller, DynamicHTML
from .compiler import reuse_this
from .settings import config

if typing.TYPE_CHECKING:
    import logging
    from pantra.common import ADict
    from pantra.components.context import Context, HTMLElement, AnyNode, ActionType
    from pantra.components.render import RenderNode
    from pantra.session import Session
    from typing import *

    refs: ADict[Context | RenderNode]
    ctx: Context
    session: Session
    logger: logging.Logger

    Locals = Dict[str, Any]

    def _(message: str, *, plural: str = None, n: int = None, ctx: str = None, many: bool = False): ...

    __all__ = ['ADict', 'Context', 'HTMLElement', 'Session', 'refs', 'ctx', 'session', 'Locals', '_', 'AnyNode',
               'Any', 'Callable', 'ClassVar', 'Generic', 'Optional', 'Tuple', 'Type', 'TypeVar', 'Union', 'AbstractSet',
               'ByteString', 'Container', 'ContextManager', 'Hashable', 'ItemsView', 'Iterable', 'Iterator', 'KeysView',
               'Mapping', 'MappingView', 'MutableMapping', 'MutableSequence', 'MutableSet', 'Sequence', 'Sized',
               'ValuesView', 'Awaitable', 'AsyncIterator', 'AsyncIterable', 'Coroutine', 'Collection', 'AsyncGenerator',
               'AsyncContextManager', 'Deque', 'Dict', 'DefaultDict', 'List', 'Set', 'FrozenSet', 'NamedTuple',
               'Generator', 'NewType', 'NoReturn', 'typing', 'WebUnits', 'logger', 'EmptyCaller', 'DynamicHTML',
               'config', 'ActionType', 'reuse_this']
