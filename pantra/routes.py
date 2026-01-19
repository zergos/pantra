import asyncio
import sys
import logging
from importlib import import_module
from pathlib import Path
import mimetypes
import traceback
from datetime import datetime

import sass

from starlette.routing import Route, WebSocketRoute, Mount
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, JSONResponse, PlainTextResponse, FileResponse, RedirectResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.staticfiles import StaticFiles

from pantra.components.template import collect_template, get_template_path, collect_styles
from pantra.patching import wipe_logger
from pantra.session import Session
from pantra.settings import config
from pantra import jsmap

logger = logging.getLogger("pantra.system")

def get(pattern: str, method: str = None):
    def inner(func):
        if not hasattr(func, "patterns"):
            func.patterns = [(pattern, method)]
        else:
            func.patterns.append((pattern, method))
        return func
    return inner

@wipe_logger
class BaseRouter:
    routes: list[Route]
    CACHE_ID = Session.gen_session_id()

    def __init__(self):
        super().__init__()
        if not config.BOOTSTRAP_FILENAME.exists():
            print(f'File `{config.BOOTSTRAP_FILENAME}` not found')
            sys.exit(1)

        self.bootstrap: str = config.BOOTSTRAP_FILENAME.read_text()

    @staticmethod
    def startup():
        if config.WORKER_SERVER.run_with_web:
            if not config.PRODUCTIVE and config.ENABLE_WATCHDOG:
                from pantra.watchers import start_observer
                start_observer()
            asyncio.create_task(Session.run_server_worker())

    def static_routes(self):
        return []

    def routes(self):
        res = []
        for func_name in dir(self):
            if func_name.startswith("_"):
                continue

            if not hasattr(func:=getattr(self, func_name), "patterns"):
                continue

            for pattern, method in func.patterns:
                if method == 'ws':
                    res.append(WebSocketRoute(pattern, func))
                else:
                    res.append(Route(pattern, func, methods=method and [method.upper()]))
        res.extend(self.static_routes())
        return res

    @staticmethod
    def forbidden(message: str) -> Response:
        return PlainTextResponse(message, 403)

    @staticmethod
    def not_found(message: str) -> Response:
        return PlainTextResponse(message, 404)

    @staticmethod
    def bad_request(message: str = '') -> Response:
        return PlainTextResponse(message, 400)

    @staticmethod
    def css(value: str) -> Response:
        return Response(value, 200, media_type="text/css")

    @get("/{app}")
    @get("/")
    async def get_main_page(self, request: Request):
        app = request.path_params.get("app")

        local_id = Session.gen_session_id()
        session_id = Session.gen_session_id()

        if not app:
            app = config.DEFAULT_APP

        try:
            app_module = import_module(f"apps.{app}")
        except ModuleNotFoundError:
            app_module = None
        app_title = getattr(app_module, "APP_TITLE", None) or config.APP_TITLE

        body = self.bootstrap.replace('{{LOCAL_ID}}', local_id)\
            .replace('{{TAB_ID}}', session_id)\
            .replace('{{WEB_PATH}}', config.WEB_PATH)\
            .replace('{{APP_TITLE}}', app_title)\
            .replace('{{CACHE_ID}}', self.CACHE_ID)

        logger.debug(f"Bootstrap page rendered {local_id}/{session_id}")
        return HTMLResponse(body)

    @get('/ws/{local_id}/{session_id}', method="ws")
    @get('/{app}/ws/{local_id}/{session_id}', method="ws")
    async def get_ws(self, websocket: WebSocket):
        local_id: str = websocket.path_params['local_id']
        session_id: str = websocket.path_params['session_id']
        app: str = websocket.path_params.get('app')

        #ws = web.WebSocketResponse(receive_timeout=config.SOCKET_TIMEOUT, max_msg_size=config.MAX_MESSAGE_SIZE,
        #                           heartbeat=config.WS_HEARTBEAT_INTERVAL)
        await websocket.accept()

        if not app:
            app = config.DEFAULT_APP

        logger.debug(
            f"WebSocket connected {{{app}}} {local_id}/{session_id}")

        lang_info = websocket.headers.get('Accept-Language', 'en')
        lang = [part.split(';')[0].replace('-', '_') for part in lang_info.split(',')]

        # session = Session(request.match_info['local_id'], session_id, ws, app, lang)

        async with config.WORKER_CLIENT(session_id, websocket, app, lang, dict(websocket.query_params)) as worker:
            while True:
                try:
                    data = await websocket.receive_bytes()
                    await worker.connection.send(data)
                except asyncio.exceptions.TimeoutError:
                    if (datetime.now() - worker.last_touch).seconds < config.SOCKET_TIMEOUT:
                        continue
                    break
                except asyncio.exceptions.CancelledError:
                    raise
                except RuntimeError as e:
                    # logger.error(f'Runtime error: {e}')
                    break
                except WebSocketDisconnect as e:
                    logger.error(f'WebSocket connection closed with exception `{e}`')
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {traceback.format_exc(-1)}")
                    break

@wipe_logger
class DevRouter(BaseRouter):
    def static_routes(self):
        res = [Mount('/css', StaticFiles(directory=config.CSS_PATH)),
               Mount('/js', StaticFiles(directory=config.JS_PATH))]
        return res

    @get('/static/{file}')
    @get('/static/${template}/{file}')
    @get('/static/@{virt_dir}/{file}')
    @get('/static/~{app}/{file}')
    async def get_media(self, request: Request):
        file_name = request.path_params.get('file')
        template_name = request.path_params.get('template')
        virt_dir = request.path_params.get('virt_dir')
        app = request.path_params.get('app')

        if '..' in Path(file_name).parts:
            return self.forbidden('`..` not allowed')

        if virt_dir:
            if virt_dir not in config.ALLOWED_DIRS:
                logger.debug(f'Directory `{virt_dir}` not found')
                return self.not_found(f'Directory `{virt_dir}` not found')
            search_path = config.ALLOWED_DIRS[virt_dir]
        elif template_name:
            if (t := collect_template(template_name[1:])) is None:
                return self.not_found(f'`{template_name[1:]}` not found')
            search_path = get_template_path(t) / config.STATIC_DIR
        elif app:
            search_path = config.APPS_PATH / app / config.STATIC_DIR
        else:
            search_path = config.COMPONENTS_PATH / config.STATIC_DIR

        file_path = search_path / file_name
        if not file_path.exists():
            logger.debug(f'File `{file_path.relative_to(config.BASE_PATH)}` not found')
            return self.not_found(f'`{file_path.name}` not found')

        logger.debug(f'File `{file_path.relative_to(config.BASE_PATH)}` requested')

        mimetype = mimetypes.guess_type(file_path)[0]
        if mimetype is None:
            mimetype = 'application/octet-stream'

        return FileResponse(file_path, media_type=mimetype, content_disposition_type="inline")


    # TODO: cache styles and join with file watcher
    @get('/css/global.css')
    async def get_global_css(self, request: Request):
        logger.debug("Collecting global components` styles")
        styles = collect_styles('Core', config.COMPONENTS_PATH, Session.error_later)
        return self.css(styles)

    @get('/css/{app}.local.css')
    async def get_local_css(self, request: Request):
        app = request.path_params['app']
        logger.debug(f"[{app}] Collecting styles")
        if not app:
            if config.DEFAULT_APP == 'Core':
                return self.css('')
            else:
                app = config.DEFAULT_APP
        app_path = config.APPS_PATH / app
        styles = collect_styles(app, app_path, Session.error_later)
        return self.css(styles)

    @get('/css/{file_name}.css')
    async def get_static_scss(self, request: Request):
        file_name = request.path_params['file_name']
        logger.debug(f"Compiling SCSS {file_name}")
        try:
            content = ''
            file_name = config.CSS_PATH / file_name
            if file_name.with_suffix('.scss').exists():
                text = file_name.with_suffix('.scss').read_text(encoding='utf-8')
                content = sass.compile(string=text, output_style='compact', include_paths=[str(config.CSS_PATH.parent)])
            elif file_name.with_suffix('.css').exists():
                content = file_name.with_suffix('.css').read_text(encoding='utf-8')
        except Exception as e:
            Session.error_later(f'{file_name}.scss> {e}')
            return self.bad_request()
        else:
            return self.css(content)

    @get('/js/' + jsmap.JS_BUNDLE_FILENAME)
    async def get_out_js(self, request: Request):
        return Response(jsmap.cache.content, media_type='application/javascript')

    @get('/js/' + jsmap.JS_BUNDLE_MAP_FILENAME)
    async def get_out_js_map(self, request: Request):
        return JSONResponse(jsmap.cache.map)


class CachedRouter(BaseRouter):
    @get('/css/.local.css')
    async def get_local_css(self, request: Request):
        return RedirectResponse(f'/css/{config.DEFAULT_APP}.local.css')

    @get('/static/@{virt_dir}/{file:path}')
    async def get_media(self, request: Request):
        file_name = request.path_params.get('file')
        virt_dir = request.path_params.get('virt_dir')

        if '..' in Path(file_name).parts:
            return self.forbidden('`..` not allowed')

        if virt_dir:
            if virt_dir not in config.ALLOWED_DIRS:
                logger.debug(f'Directory `{virt_dir}` not found')
                return self.not_found(f'directory `{virt_dir}` not found')
            search_path = config.ALLOWED_DIRS[virt_dir]
        else:
            return self.not_found(f'Directory not specified')

        file_path = search_path / file_name
        if not file_path.exists():
            logger.debug(f'File `{file_path.relative_to(config.BASE_PATH)}` not found')
            return self.not_found(f'`{file_name}` not found')

        logger.debug(f'File `{file_path.relative_to(config.BASE_PATH)}` requested')

        mimetype = mimetypes.guess_type(file_path)[0]
        if mimetype is None:
            mimetype = 'application/octet-stream'

        return FileResponse(file_path, media_type=mimetype, content_disposition_type="inline")

    def static_routes(self):
        res = [Mount('/css', StaticFiles(directory=config.CACHE_PATH / 'css')),
               Mount('/js', StaticFiles(directory=config.CACHE_PATH / 'js')),
               Mount('/static', StaticFiles(directory=config.CACHE_PATH / config.STATIC_DIR))
               ]
        return res
