from importlib import import_module

__all__ = ['config']

class Config:
    def __init__(self):
        self._inited: bool = False

    def init(self):
        mods = ['pantra.defaults', 'apps.config']
        for mod in mods:
            try:
                settings = import_module(mod)
            except ModuleNotFoundError:
                continue
            for attr in dir(settings):
                if attr.isupper():
                    setattr(self, attr, getattr(settings, attr))
        self._inited = True

        if self.ENABLE_LOGGING:
            for attr in dir(self):
                if attr.isupper():
                    print(f'{attr} = {getattr(self, attr)}')

    def __getattr__(self, item):
        if item.isupper() and not self._inited:
            self.init()
        return super().__getattribute__(item)


config: Config = Config()
