import typing
from importlib import import_module
import importlib.util
import logging
import os
import string
import ast
import sys
from pathlib import Path
import re

from .defaults import Config

__all__ = ['config', 'safe_config', 'logger']
logger = logging.getLogger("pantra.system")

RE_CLS_PATH = re.compile(r"^\{([a-z_][a-z0-9_]*)(\.[a-z_][a-z0-9_]*)*(:[a-z_][a-z0-9_]*)?}$", re.IGNORECASE)

class AbstractConfig(Config):
    def _read_env_data(self):
        for env_var, env_value in os.environ.items():
            if env_var.startswith("PANTRA_"):
                logger.warning(f'Env: {env_var}')

                def parse_value(env_value):
                    if env_value[0] in string.digits:
                        return ast.literal_eval(env_value)
                    elif env_value == 'None':
                        return None
                    elif env_value.lower() in ("true", "false"):
                        return bool(env_value)
                    else:
                        return env_value

                setattr(self, env_var[7:], parse_value(env_value))

    def string_to_object(self, var_name: typing.Any):
        try:
            value = object.__getattribute__(self, var_name)
            if isinstance(value, str):
                value = value[1:-1]
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
    def read_module_safely(self, module: str):
        spec = importlib.util.find_spec(module)
        if spec is None:
            return

        source = Path(spec.origin).read_text()

        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "AppConfig":
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        if (isinstance(item.target, ast.Name) and item.target.id.isupper()
                            and isinstance(item.value, ast.Constant)):
                            setattr(self, item.target.id, item.value.value)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if (isinstance(target, ast.Name) and target.id.isupper()
                                and isinstance(item.value, ast.Constant)):
                                setattr(self, target.id, item.value.value)

    def __init__(self):
        self.read_module_safely("apps.config")
        self._read_env_data()

class LazyConfig(AbstractConfig):
    def __init__(self):
        self._inited: bool = False
        self._changed_pars: list[str] = []

    def _read_module_import(self, mod: str):
        try:
            settings = import_module(mod)
        except ModuleNotFoundError:
            import sys
            logger.warning(f"Module `{mod}` is not found in {sys.path}")
        else:
            for attr in dir(settings):
                if attr.isupper():
                    setattr(self, attr, getattr(settings, attr))
                elif attr == 'AppConfig':
                    for k, v in getattr(settings, attr).__dict__.items():
                        if k.isupper():
                            setattr(self, k, v)

    def _late_init(self):
        self._read_module_import('apps.config')
        if safe_config.BASE_PATH not in sys.path:
            sys.path.append(str(safe_config.BASE_PATH))

        self._inited = True

        for var_name in dir(self):
            if var_name.isupper():
                value = getattr(self, var_name)
                if isinstance(value, str) and RE_CLS_PATH.match(value):
                    self.string_to_object(var_name)

        if not self.hasattr("WORKER_SERVER") and self.hasattr("WORKERS_MODULE"):
            workers = self.WORKERS_MODULE
            setattr(self, "WORKER_SERVER",  workers.WorkerServer)
            setattr(self, "WORKER_CLIENT",  workers.WorkerClient)

        self._read_env_data()

        if self.RUN_CACHED:
            from pantra.cached.renderer import RendererCached
            from pantra.routes import CachedRouter
            config.DEFAULT_RENDERER = RendererCached
            config.ROUTER_CLASS = CachedRouter
            config.BOOTSTRAP_FILENAME = config.CACHE_PATH / 'bootstrap.html'
            config.COMPONENTS_PATH = config.CACHE_PATH / 'core'
            config.APPS_PATH = config.CACHE_PATH / 'apps'

        if not self.WIPE_LOGGING:
            self.SETUP_LOGGER(getattr(logging, self.LOG_LEVEL.upper()))

            for attr in self._changed_pars:
                value = object.__getattribute__(self, attr)
                if callable(value):
                    logger.debug(f'{attr} = func()')
                else:
                    logger.debug(f'{attr} = {value!r}')
            logger.debug('----')

    def __getattribute__(self, item: str):
        if item.isupper() and not self._inited:
            self._late_init()
        return super().__getattribute__(item)

    def __getitem__(self, item):
        if not self._inited:
            self._late_init()
        if item.isupper():
            return object.__getattribute__(self, item)
        else:
            raise KeyError(item)

    def __setattr__(self, key, value):
        try:
            if not self._inited and key.isupper() and value != object.__getattribute__(self, key):
                self._changed_pars.append(key)
        except AttributeError:
            pass
        super().__setattr__(key, value)

safe_config: SafeConfig = SafeConfig()  #: contains constant values only
config: LazyConfig = LazyConfig() #: contains all values, but initializes upon request
