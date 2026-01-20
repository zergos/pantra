import typing
from importlib import import_module
import logging
import os
import string
import ast
import sys

__all__ = ['config', 'safe_config', 'logger']
logger = logging.getLogger("pantra.system")

class AbstractConfig:
    def read_modules(self, mods: list[str]):
        for mod in mods:
            try:
                settings = import_module(mod)
            except ModuleNotFoundError:
                import sys
                logger.warning(f"Module `{mod}` is not found in {sys.path}")
                continue
            for attr in dir(settings):
                if attr.isupper():
                    setattr(self, attr, getattr(settings, attr))

    def read_env_data(self):
        for env_var, env_value in os.environ.items():
            if env_var.startswith("PANTRA_"):
                logger.warning(f'Env: {env_var}')

                def parse_value(env_value):
                    if ',' in env_value:
                        return [parse_value(val) for val in env_value.split(',')]
                    elif env_value[0] in string.digits:
                        return ast.literal_eval(env_value)
                    elif env_value == 'None':
                        return None
                    else:
                        return env_value

                setattr(self, env_var[7:], parse_value(env_value))

    def string_to_object(self, var_name: typing.Any):
        try:
            value = object.__getattribute__(self, var_name)
            if isinstance(value, str):
                chunks = value.split(":")
                module_name = chunks[0]
                func_name = chunks[1] if len(chunks) > 1 else None
                mod = import_module(module_name)
                if func_name is not None:
                     setattr(self, var_name, getattr(mod, func_name))
                else:
                    setattr(self, var_name, mod)
        except AttributeError:
            pass

    def hasattr(self, attr):
        return attr in self.__dict__

    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            return None

class SafeConfig(AbstractConfig):
    def __init__(self):
        self.read_modules(['apps.config'])
        self.read_env_data()

class LazyConfig(AbstractConfig):
    def __init__(self):
        self._inited: bool = False

    def init(self):
        self.read_modules(['pantra.defaults', 'apps.config'])
        if self.BASE_PATH not in sys.path:
            sys.path.append(str(self.BASE_PATH))

        self._inited = True

        for var_name in ("WORKERS_MODULE", "WORKER_SERVER", "WORKER_CLIENT", "DEFAULT_RENDERER", "ROUTER_CLASS"):
            self.string_to_object(var_name)

        if not self.hasattr("WORKER_SERVER") and self.hasattr("WORKERS_MODULE"):
            workers = self.WORKERS_MODULE
            setattr(self, "WORKER_SERVER",  workers.WorkerServer)
            setattr(self, "WORKER_CLIENT",  workers.WorkerClient)

        self.read_env_data()

        if self.RUN_CACHED:
            from pantra.cached.renderer import RendererCached
            from pantra.routes import CachedRouter
            config.DEFAULT_RENDERER = RendererCached
            config.ROUTER_CLASS = CachedRouter
            config.BOOTSTRAP_FILENAME = config.CACHE_PATH / 'bootstrap.html'
            config.COMPONENTS_PATH = config.CACHE_PATH / 'core'
            config.APPS_PATH = config.CACHE_PATH / 'apps'

        if self.WIPE_LOGGING:
            self.SETUP_LOGGER(getattr(logging, self.LOG_LEVEL.upper()))

            for attr in dir(self):
                if attr.isupper():
                    logger.debug(f'{attr} = {object.__getattribute__(self, attr)}')
            logger.debug('----')

    def __getattr__(self, item: str):
        if item.isupper() and item not in self.__dict__ and not self._inited:
            self.init()
        return super().__getattr__(item)

safe_config: SafeConfig = SafeConfig()
config: LazyConfig = LazyConfig()
