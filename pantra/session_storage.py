from __future__ import annotations

import typing
import time
from abc import ABC, abstractmethod
from typing import NamedTuple
from weakref import WeakValueDictionary

from pantra.settings import config

if typing.TYPE_CHECKING:
    from typing import Any, Mapping
    from .session import Session


class SessionStorage(ABC):
    """Abstract session storage.

    Allows to keep user values between sessions.
    """
    __slots__ = ("_binding_dicts", "_binding_keys", "_session")

    def __init__(self, session: Session):
        self._binding_dicts: WeakValueDictionary[str, dict[str, Any]] = WeakValueDictionary()
        self._binding_keys: dict[str, str] = {}
        self._session = session

    @abstractmethod
    def _load(self) -> dict[str, Any]:
        """Load session data from the specific storage"""

    @abstractmethod
    def _put(self, data: dict[str, Any]):
        """Put session data to the specific storage"""

    def add_binding(self, name: str, dict_ref: dict[str, Any], key: str):
        """Bind storage record to the specific key of the dictionary

        Arguments:
            name: The name of the record
            dict_ref: The dictionary to bind
            key: The key (of `dict_ref`) to bind
        """
        if name not in self._binding_dicts:
            self._binding_dicts[name] = dict_ref
            self._binding_keys[name] = key
        if name in self._session.state:
            dict_ref[key] = self._session[name]

    def gather(self):
        """Gather all bound values from dictionaries to set session state"""
        for name, binding in list(self._binding_dicts.items()):
            self._session[name] = binding[self._binding_keys[name]]

    def distribute(self):
        """Distribute values from session state to bound dictionaries"""
        for name, binging in list(self._binding_dicts.items()):
            binging[self._binding_keys[name]] = self._session[name]

    def reload(self):
        """Reload session state"""
        self._session.state.update(self._load())

    def sync(self):
        """Sync session state"""
        self._put({k: v for k, v in self._session.state.items() if k in self._binding_dicts})

class NullSessionStorage(SessionStorage):
    """Default session storage behavior - just keep in session state"""
    def _load(self) -> dict[str, typing.Any]:
        return {}

    def _put(self, data: dict[str, typing.Any]):
        pass

class ShelveSessionStorage(SessionStorage):
    """Use `shelve <https://docs.python.org/3/library/shelve.html>`__ to keep user data"""
    def __init__(self, session: Session):
        super().__init__(session)
        session_path = config.APPS_PATH / session.app / "storage"
        if not session_path.exists():
            session_path.mkdir()

    def _load(self) -> dict[str, typing.Any]:
        import shelve
        try:
            from dbm.gnu import error
            exc = error
        except ModuleNotFoundError:
            exc = Exception

        filename = config.APPS_PATH / self._session.app / "storage" / (self._session.user or "common")
        while True:
            try:
                with shelve.open(str(filename)) as db:
                    return dict(db.items())
                break
            except exc:
                time.sleep(1)

    def _put(self, data: dict[str, typing.Any]):
        import shelve
        try:
            from dbm.gnu import error
            exc = error
        except ModuleNotFoundError:
            exc = Exception

        filename = config.APPS_PATH / self._session.app / "storage" / (self._session.user or "common")
        while True:
            try:
                with shelve.open(str(filename)) as db:
                    for name, value in data.items():
                        db[name] = value
                break
            except exc:
                time.sleep(1)
