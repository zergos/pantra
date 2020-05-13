import typing

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from components.loader import refresh_template
from core.defaults import APPS_PATH, COMPONENTS_PATH

__all__ = ['start_observer', 'stop_observer']

observer: typing.Optional[Observer] = None


class AppFilesEventHandler(PatternMatchingEventHandler):

    def __init__(self):
        super().__init__(['*.html'])

    def on_modified(self, event):
        print(f'file {event.src_path} changed, refreshing')
        refresh_template(event.src_path)


def start_observer():
    global observer
    observer = Observer()
    observer.schedule(AppFilesEventHandler(), APPS_PATH, True)
    observer.schedule(AppFilesEventHandler(), COMPONENTS_PATH, True)
    observer.start()


def stop_observer():
    observer.stop()
    observer.join()

