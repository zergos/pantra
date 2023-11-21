import asyncio
import typing
import threading
import queue
import functools
import time
from dataclasses import dataclass, field
import logging

from .common import raise_exception_in_thread
from .patching import wipe_logger
from .settings import config

logger = logging.getLogger('pantra.system')

# Thread workers

workers: typing.Dict[str, 'WorkerStat'] = {}


@dataclass
class WorkerStat:
    active: bool = field(default=False)
    last_time: float = field(default=0)
    finish_flag: int = field(default=0)


task_queue: typing.Optional[queue.Queue] = None


def task_processor():
    try:
        ident = threading.current_thread().name
        if ident not in workers:
            workers[ident] = WorkerStat()
        while True:
            try:
                func, args, kwargs = task_queue.get(timeout=5)
            except queue.Empty:
                if workers[ident].finish_flag:
                    workers[ident].finish_flag = -1
                    break
                continue
            if func is None: break
            workers[ident].last_time = time.perf_counter()
            workers[ident].active = True
            func(*args, **kwargs)
            workers[ident].last_time = time.perf_counter()
            workers[ident].active = False
    except SystemExit:
        logger.error('thread timeout')


@wipe_logger
def stat_thread():
    while True:
        time.sleep(1)
        tick = time.perf_counter()
        last_tick = 0
        for k, v in list(workers.items()):  # type: str, WorkerStat
            if v.finish_flag != 0:
                if v.finish_flag == -1:
                    del workers[k]
                continue
            if v.active and tick - v.last_time > config.THREAD_TIMEOUT:
                if len(workers) > config.MIN_TASK_THREADS:
                    logger.warning(f"Thread removing `f{k}`")
                    raise_exception_in_thread(k)
                    del workers[k]
            elif not v.active and tick - v.last_time > config.KILL_THREAD_LAG:
                v.finish_flag = 1
            if tick > last_tick:
                last_tick = tick
        if not task_queue.empty() and last_tick and tick - last_tick > config.CREAT_THREAD_LAG:
            logger.warning(f'New thread creation X#{len(workers)}')
            threading.Thread(target=task_processor, name=f'X#{len(workers)}').start()


def thread_worker(func):
    @functools.wraps(func)
    def res(*args, **kwargs):
        task_queue.put((func, args, kwargs))
    return res


def start_task_workers():
    global task_queue
    task_queue = queue.Queue()
    for i in range(config.MIN_TASK_THREADS):
        threading.Thread(target=task_processor, name=f'#{i}').start()


def stop_task_workers():
    for i in range(len(workers)):
        task_queue.put((None, None, None))

# Async workers

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
