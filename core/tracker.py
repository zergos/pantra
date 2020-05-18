import typing
import os
from datetime import datetime

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from core.defaults import APPS_PATH, COMPONENTS_PATH

__all__ = ['start_observer', 'stop_observer']

observer: typing.Optional[Observer] = None


class AppFilesEventHandler(PatternMatchingEventHandler):

    def __init__(self, templates, sessions, code_base):
        super().__init__(['*.html', '*.py'])
        self.templates = templates
        self.sessions = sessions
        self.code_base = code_base

    def refresh_template(self, filename: str):
        if filename.endswith('.html'):
            for k, v in list(self.templates.items()):
                if v and v.filename == filename:
                    # self.sessions.error_later(f'component {k} has updated')
                    del self.templates[k]
        else:
            if filename in self.code_base:
                # self.sessions.error_later(f'namespace {os.path.basename(filename)} has updated')
                del self.code_base[filename]


    def on_modified(self, event):
        print(f'{datetime.now():%x %X}> file {event.src_path} changed, refreshing')
        self.refresh_template(event.src_path)


def start_observer(templates, sessions, code_base):
    global observer
    observer = Observer()
    observer.schedule(AppFilesEventHandler(templates, sessions, code_base), APPS_PATH, True)
    observer.schedule(AppFilesEventHandler(templates, sessions, code_base), COMPONENTS_PATH, True)
    observer.start()


def stop_observer():
    observer.stop()
    observer.join()

