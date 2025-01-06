import sys
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

    def __init__(self, templates, code_base):
        super().__init__(['*.html', '*.py'])
        self.templates = templates
        self.code_base = code_base

    @wipe_logger
    def refresh_template(self, filename: Path):
        if filename.suffix == '.html':
            hex_digest = hashlib.md5(filename.read_bytes()).hexdigest()
            for k, v in list(self.templates.items()):  # type: str, HTMLTemplate
                if v and v.filename == filename and v.hex_digest != hex_digest:
                    logger.warning(f'File `{filename.relative_to(config.BASE_PATH)}` changed, refreshing')
                    del self.templates[k]
                    break
        else:
            logger.warning(f'File `{filename.relative_to(config.BASE_PATH)}` changed, refreshing')
            if filename in self.code_base:
                del self.code_base[str(filename)]
            else:
                module_name = '.'.join(filename.relative_to(config.BASE_PATH).parts).removesuffix('.py').removesuffix('.__init__')
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    del sys.modules[module_name.rsplit('.', 1)[0]]

    def on_modified(self, event):
        self.refresh_template(Path(event.src_path))


@wipe_logger
def start_observer():
    global observer

    from .compiler import code_base
    from .components.loader import templates

    logger.info("Starting files watchers")
    observer = Observer()
    observer.daemon = True
    observer.schedule(AppFilesEventHandler(templates, code_base), config.APPS_PATH, True)
    observer.schedule(AppFilesEventHandler(templates, code_base), config.COMPONENTS_PATH, True)
    observer.start()


def stop_observer():
    observer.stop()
    observer.join()

