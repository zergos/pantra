from __future__ import annotations

import typing
import time
from abc import ABC, abstractmethod
from typing import NamedTuple

if typing.TYPE_CHECKING:
    from .session import Session


class BindingTuple(NamedTuple):
    dict_ref: dict
    key: str


class SessionStorage(ABC):
    bindings: dict[str, BindingTuple]
    session: Session

    def __init__(self, session: Session):
        self.bindings = {}
        self.session = session

    @abstractmethod
    def load(self): ...

    @abstractmethod
    def dump(self): ...

    def add_binding(self, name: str, dict_ref: dict, key: str):
        if name not in self.bindings:
            self.bindings[name] = BindingTuple(dict_ref, key)
        if name in self.session.state:
            dict_ref[key] = self.session[name]

    def gather(self):
        for name, binding in self.bindings.items():
            self.session[name] = binding.dict_ref[binding.key]

    def distribute(self):
        for name, binging in self.bindings.items():
            binging.dict_ref[binging.key] = self.session[name]


class ShelveSessionStorage(SessionStorage):
    def __init__(self, session: Session):
        super().__init__(session)
        self.filename = session.app_path / "storage" / (session.user or "common")
        if not self.filename.parent.exists():
            self.filename.parent.mkdir()

    def load(self):
        import shelve
        try:
            from dbm.gnu import error
            exc = error
        except ModuleNotFoundError:
            exc = Exception

        while True:
            try:
                with shelve.open(str(self.filename)) as db:
                    self.session.state |= dict(db.items())
                break
            except exc:
                time.sleep(1)

    def dump(self):
        import shelve
        try:
            from dbm.gnu import error
            exc = error
        except ModuleNotFoundError:
            exc = Exception

        while True:
            try:
                with shelve.open(str(self.filename)) as db:
                    for name in self.bindings:
                        db[name] = self.session[name]
                break
            except exc:
                time.sleep(1)

