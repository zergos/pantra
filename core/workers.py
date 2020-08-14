import asyncio
import typing
import threading
import queue
import functools
import time
from dataclasses import dataclass, field

from .common import raise_exception_in_thread
from .defaults import *

# Thread tasks

tasks: typing.Dict[int, 'WorkerStat'] = {}


@dataclass
class WorkerStat:
    active: bool = field(default=False)
    last_time: float = field(default=0)
    finish_flag: int = field(default=0)


task_queue: typing.Optional[queue.Queue] = None


def task_processor():
    try:
        ident = threading.currentThread().ident
        if ident not in tasks:
            tasks[ident] = WorkerStat()
        while True:
            try:
                func, args, kwargs = task_queue.get(timeout=5)
            except queue.Empty:
                if tasks[ident].finish_flag:
                    tasks[ident].finish_flag = -1
                    break
                continue
            if func is None: break
            tasks[ident].last_time = time.perf_counter()
            tasks[ident].active = True
            func(*args, **kwargs)
            tasks[ident].last_time = time.perf_counter()
            tasks[ident].active = False
    except SystemExit:
        print('thread timeout')


def stat_thread():
    while True:
        time.sleep(1)
        tick = time.perf_counter()
        last_tick = 0
        for k, v in list(tasks.items()):  # type: int, WorkerStat
            if v.finish_flag != 0:
                if v.finish_flag == -1:
                    del tasks[k]
                continue
            if v.active and tick - v.last_time > THREAD_TIMEOUT:
                if len(tasks) > MIN_TASK_THREADS:
                    raise_exception_in_thread(k)
                    del tasks[k]
            elif not v.active and tick - v.last_time > KILL_THREAD_LAG:
                v.finish_flag = 1
            if tick > last_tick:
                last_tick = tick
        if not task_queue.empty() and last_tick and tick - last_tick > CREAT_THREAD_LAG:
            threading.Thread(target=task_processor).start()


def thread_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        task_queue.put((func, args, kwargs))
    return res


def start_task_workers():
    global task_queue
    task_queue = queue.Queue()
    for i in range(MIN_TASK_THREADS):
        threading.Thread(target=task_processor).start()


def stop_task_workers():
    for i in range(len(tasks)):
        task_queue.put((None, None, None))

# Async tasks

async_loop: typing.Optional[asyncio.BaseEventLoop] = None


def async_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        if async_loop._thread_id == threading.current_thread().ident:
            return func(*args, **kwargs)
        asyncio.run_coroutine_threadsafe(func(*args, **kwargs), async_loop)
    return res


def init_async_worker():
    global async_loop
    async_loop = asyncio.get_running_loop()
