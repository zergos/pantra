from importlib import import_module

__all__ = ['config']

class Config:
    def __init__(self):
        self._inited: bool = False

    def init(self):
        mods = ['pantra.defaults', 'app.config']
        for mod in mods:
            try:
                settings = import_module(mod)
            except ModuleNotFoundError:
                continue
            for attr in dir(settings):
                if attr.upper():
                    setattr(self, attr, getattr(settings, attr))
        self._inited = True

    def __getattr__(self, item):
        if item.upper() and not self._inited:
            self.init()
        super().__getattribute__(item)


config: Config = Config()
