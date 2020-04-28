import asyncio
import typing
import threading
import queue
import functools

from core.defaults import TASK_THREADS

# Thread tasks

task_queue: typing.Optional[queue.Queue] = None


def task_processor():
    while True:
        func, args, kwargs = task_queue.get()
        if func is None: break
        func(*args, **kwargs)


def thread_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        task_queue.put((func, args, kwargs))
    return res


def start_task_workers():
    global task_queue
    task_queue = queue.Queue()
    for i in range(TASK_THREADS):
        threading.Thread(target=task_processor)


def stop_task_workers():
    for i in range(TASK_THREADS):
        task_queue.put((None, None, None))

# Async tasks

async_loop: typing.Optional[asyncio.BaseEventLoop] = None


def async_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        async_loop.create_task(func(*args, **kwargs))
    return res


def init_async_worker():
    global async_loop
    async_loop = asyncio.get_running_loop()
