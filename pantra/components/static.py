from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pantra.settings import config

__all__ = ['get_static_url']

def get_static_url(app: str, template_file_name: Path, sub_dir: str | None, file_name: str) -> str:
    try:
        return get_static_url_cached(app, template_file_name, sub_dir, file_name)
    except FileNotFoundError:
        return '#'

@lru_cache(maxsize=1000)
def get_static_url_cached(app: str, template_file_name: Path, sub_dir: str | None, file_name: str) -> str:
    if sub_dir and sub_dir in config.ALLOWED_DIRS:
        path = config.ALLOWED_DIRS[sub_dir] / file_name
        if path.exists():
            return config.WEB_PATH + '/'.join(['', '$' + sub_dir, '~', file_name])
        else:
            raise FileNotFoundError(file_name)

    # omit 'static' part
    if sub_dir and sub_dir != config.STATIC_DIR:
        search_name = config.STATIC_DIR + '/' + sub_dir + '/' + file_name
        web_name = sub_dir + '/' + file_name
    else:
        search_name = config.STATIC_DIR + '/' + file_name
        web_name = file_name

    # check relative to component
    path = template_file_name.parent / search_name
    if path.exists():
        return config.WEB_PATH + '/'.join(['', template_file_name.name, '~', web_name])
    else:
        # relative to app
        path = config.APPS_PATH / app / search_name
        if path.exists():
            return config.WEB_PATH + '/'.join(['', app, '~', web_name])
        else:
            # relative to components base
            path = config.COMPONENTS_PATH / search_name
            if path.exists():
                return config.WEB_PATH + '/'.join(['', '~', web_name])
            else:
                raise FileNotFoundError(search_name)
