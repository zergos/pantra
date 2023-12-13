import hashlib
import typing
import logging
import hashlib
from pathlib import Path
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from .settings import config
from .patching import wipe_logger

if typing.TYPE_CHECKING:
    from .components.loader import HTMLTemplate

__all__ = ['start_observer', 'stop_observer']

observer: typing.Optional[Observer] = None
logger = logging.getLogger("pantra.system")


class AppFilesEventHandler(PatternMatchingEventHandler):

    def __init__(self, templates, sessions, code_base):
        super().__init__(['*.html', '*.py'])
        self.templates = templates
        self.sessions = sessions
        self.code_base = code_base

    @wipe_logger
    def refresh_template(self, filename: str, hex_digest: str):
        if filename.endswith('.html'):
            for k, v in list(self.templates.items()):  # type: str, HTMLTemplate
                if v and v.filename == filename and v.hex_digest != hex_digest:
                    # self.sessions.error_later(f'component {k} has updated')
                    #logger.warning(f'File `{Path(filename).relative_to(BASE_PATH)}` changed, refreshing')
                    del self.templates[k]
        else:
            if filename in self.code_base:
                # self.sessions.error_later(f'namespace {os.path.basename(filename)} has updated')
                del self.code_base[filename]

    def on_modified(self, event):
        hex_digest = hashlib.md5(Path(event.src_path).read_bytes()).hexdigest()
        self.refresh_template(event.src_path, hex_digest)


def start_observer(templates, sessions, code_base):
    global observer

    observer = Observer()
    observer.daemon = True
    observer.schedule(AppFilesEventHandler(templates, sessions, code_base), config.APPS_PATH, True)
    observer.schedule(AppFilesEventHandler(templates, sessions, code_base), config.COMPONENTS_PATH, True)
    observer.start()


def stop_observer():
    observer.stop()
    observer.join()

