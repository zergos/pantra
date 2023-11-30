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

        if self.ENABLE_LOGGING:
            for attr in dir(self):
                if attr.isupper():
                    logger.warning(f'{attr} = {getattr(self, attr)}')
            logger.warning('----')

    def __getattr__(self, item):
        if item.isupper() and not self._inited:
            self.init()
        return super().__getattribute__(item)


config: Config = Config()
