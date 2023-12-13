import asyncio
import functools
import threading


def thread_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        from ..session import Session
        Session.server_worker.task_queue.put((func, args, kwargs))
    return res


def async_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        from ..session import Session
        if Session.server_worker.async_loop._thread_id == threading.current_thread().ident:
            return func(*args, **kwargs)
        asyncio.run_coroutine_threadsafe(func(*args, **kwargs), Session.server_worker.async_loop)
    return res
