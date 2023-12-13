from importlib import import_module
import logging

__all__ = ['config']
logger = logging.getLogger("pantra.init")


class Config:
    def __init__(self):
        self._inited: bool = False

    def init(self):
        mods = ['pantra.defaults', 'apps.config']
        for mod in mods:
            try:
                settings = import_module(mod)
                logger.warning(f"Config `{mod}` loaded")
            except ModuleNotFoundError:
                import sys
                logger.warning(f"Module `{mod}` is not found in {sys.path}")
                continue
            for attr in dir(settings):
                if attr.isupper():
                    setattr(self, attr, getattr(settings, attr))
                    if attr == "BASE_PATH":
                        import sys
                        sys.path.append(str(settings.BASE_PATH))

        self._inited = True

        if not hasattr(self, "WORKER_SERVER") and hasattr(self, "WORKERS_MODULE"):
            try:
                workers = import_module(self.WORKERS_MODULE)
                logger.warning(f"Workers module `{self.WORKERS_MODULE}` loaded")
            except ModuleNotFoundError:
                import sys
                logger.warning(f"Module `{self.WORKERS_MODULE}` is not found in {sys.path}")
                raise
            else:
                setattr(self, "WORKER_SERVER",  workers.WorkerServer)
                setattr(self, "WORKER_CLIENT",  workers.WorkerClient)

        if self.ENABLE_LOGGING:
            if hasattr(self, "SETUP_LOGGER"):
                self.SETUP_LOGGER()

            for attr in dir(self):
                if attr.isupper():
                    logger.warning(f'{attr} = {getattr(self, attr)}')
            logger.warning('----')

    def __getattr__(self, item):
        if item.isupper() and not self._inited:
            self.init()
        return super().__getattribute__(item)


config: Config = Config()
