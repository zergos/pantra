import typing
from datetime import datetime

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from core.defaults import APPS_PATH, COMPONENTS_PATH

__all__ = ['start_observer', 'stop_observer']

observer: typing.Optional[Observer] = None


class AppFilesEventHandler(PatternMatchingEventHandler):

    def __init__(self, templates, sessions):
        super().__init__(['*.html'])
        self.templates = templates
        self.sessions = sessions

    def refresh_template(self, filename: str):
        for k, v in list(self.templates.items()):
            if v and v.filename == filename:
                self.sessions.error_later(f'component {k} has updated')
                del self.templates[k]

    def on_modified(self, event):
        print(f'{datetime.now():%x %X}> file {event.src_path} changed, refreshing')
        self.refresh_template(event.src_path)


def start_observer(templates, sessions):
    global observer
    observer = Observer()
    observer.schedule(AppFilesEventHandler(templates, sessions), APPS_PATH, True)
    observer.schedule(AppFilesEventHandler(templates, sessions), COMPONENTS_PATH, True)
    observer.start()


def stop_observer():
    observer.stop()
    observer.join()

