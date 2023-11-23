from queue import Queue
import time
import logging

from .gen import make
from ..settings import config
from ..patching import wipe_logger

__all__ = ['cache']

logger = logging.getLogger("pantra.system")

@wipe_logger
class AllJSCache:
    def __init__(self):
        self.content: str | None = None
        self.map: str | None = None
        self._q = Queue(1)

    def _reset(self):
        logger.debug("Reset JS bundle")
        self.content = None
        self.map = None

    def _update(self):
        logger.debug("Building JS bundle")
        self.content, self.map = make(config.JS_PATH)

    def __getattribute__(self, item: str):
        if item.startswith("_"):
            return super().__getattribute__(item)

        while True:
            if self._q.full():
                time.sleep(1)
                continue

            content = super().__getattribute__(item)

            if content is None:
                self._q.put("BLOCK")
                self._update()
                self._q.get()
                self._q.task_done()
                continue

            return content

cache = AllJSCache()
