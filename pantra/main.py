import asyncio
import os
import sys
import traceback
import mimetypes
import logging
from importlib import import_module
from pathlib import Path

import aiofiles
from aiohttp import web, WSMsgType, WSMessage
import sass

from .components.loader import collect_styles, templates
from .serializer import serializer
from .settings import config
from .patching import wipe_logger
from .session import Session
from .protocol import Messages
from . import jsmap

__all__ = ['run']

routes = web.RouteTableDef()
logger = logging.getLogger('pantra.system')

CACHE_ID = Session.gen_session_id()


@routes.get(r'/{app:\w*}')
@wipe_logger
async def get_main_page(request: web.Request):
    local_id = Session.gen_session_id()
    session_id = Session.gen_session_id()

    app = request.match_info['app']
    if not app:
        app = config.DEFAULT_APP

    try:
        app_module = import_module(f"apps.{app}")
    except ModuleNotFoundError:
        app_module = None
    app_title = getattr(app_module, "APP_TITLE", None) or config.APP_TITLE

    body = bootstrap.replace('{{LOCAL_ID}}', local_id)\
        .replace('{{TAB_ID}}', session_id)\
        .replace('{{WEB_PATH}}', config.WEB_PATH)\
        .replace('{{APP_TITLE}}', app_title)\
        .replace('{{CACHE_ID}}', CACHE_ID)

    logger.debug(f"Bootstrap page rendered {local_id}/{session_id}")
    return web.Response(body=body, content_type='text/html')


@routes.get(r'/{app:\w*}/~/{file:.+}')
@routes.get(r'/~/{file:.+}')
async def get_media(request: web.Request):
    app: str = request.match_info.get('app', None)
    if not app:
        search_path = config.COMPONENTS_PATH
    elif app[0].isupper():
        search_path = Path(templates[app].filename).parent
    else:
        search_path = config.APPS_PATH / app

    file_path = search_path / config.STATIC_DIR / request.match_info['file']
    if not file_path.exists():
        logger.debug(f'File `{file_path.relative_to(config.BASE_PATH)}` not found')
        return web.Response(body=f'File `{file_path.name}` not found', status=404)

    logger.debug(f'File `{file_path.relative_to(config.BASE_PATH)}` requested')

    headers = {
        "Content-disposition": f"attachment; filename={file_path.name}",
        "Content-type": mimetypes.guess_type(file_path)[0],
    }
    response = web.StreamResponse(headers=headers)
    await response.prepare(request)

    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            chunk = await f.read(2 ** 16)
            if not chunk:
                break
            await response.write(chunk)

    await response.write_eof()
    return response


@routes.get(r'/{app:\w*}/ws/{local_id:\w+}/{session_id:\w+}')
@wipe_logger
async def get_ws(request: web.Request):
    ws = web.WebSocketResponse(receive_timeout=config.SOCKET_TIMEOUT, max_msg_size=config.MAX_MESSAGE_SIZE)
    await ws.prepare(request)

    session_id = request.match_info['session_id']
    app = request.match_info['app']
    if not app:
        app = config.DEFAULT_APP

    logger.debug(f"WebSocket connected {{{app}}} {request.match_info['local_id']}/{request.match_info['session_id']}")

    lang_info = request.headers.get('Accept-Language', 'en')
    lang = [part.split(';')[0].replace('-', '_') for part in lang_info.split(',')]

    #session = Session(request.match_info['local_id'], session_id, ws, app, lang)

    async with config.WORKER_CLIENT(session_id, ws, app, lang) as worker:
        try:
            async for msg in ws:  # type: WSMessage
                if msg.type == WSMsgType.BINARY:
                    await worker.connection.send(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket connection closed with exception {ws.exception()}')
        except asyncio.exceptions.TimeoutError:
            pass
        except asyncio.exceptions.CancelledError:
            raise
        except:
            logger.error(f"WebSocket error: {traceback.format_exc(-1)}")
            message = serializer.encode(Messages.error(traceback.format_exc()))
            await worker.connection.send(message)

    return ws


# TODO: cache styles and join with file watcher
@routes.get(r'/css/global.css')
@wipe_logger
async def get_global_css(request: web.Request):
    logger.debug("Collecting global components` styles")
    styles = collect_styles('Core', config.COMPONENTS_PATH, Session.error_later)
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{app:\w*}.local.css')
@wipe_logger
async def get_local_css(request: web.Request):
    app = request.match_info['app']
    logger.debug(f"[{app}] Collecting styles")
    if not app:
        if config.DEFAULT_APP == 'Core':
            return web.Response(content_type='text/css')
        else:
            app = config.DEFAULT_APP
    app_path = config.APPS_PATH / app
    styles = collect_styles(app, app_path, Session.error_later)
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{name:.+?}.scss')
@wipe_logger
async def get_static_scss(request: web.Request):
    file_name = request.match_info['name']
    logger.debug(f"Compiling SCSS {file_name}")
    try:
        file_name = config.CSS_PATH / file_name
        text = file_name.with_suffix('.scss').read_text(encoding='utf-8')
        css = sass.compile(string=text, output_style='compact', include_paths=[str(config.CSS_PATH)])
    except Exception as e:
        Session.error_later(f'{file_name}.scss> {e}')
        return web.Response(status=404)
    else:
        return web.Response(body=css, content_type='text/css')


@routes.get(r'/js/'+jsmap.OUT_NAME)
async def get_out_js(request: web.Request):
    return web.Response(body=jsmap.cache.content, content_type='application/javascript', headers={'SourceMap': jsmap.OUT_NAME+'.map'})

@routes.get(r'/js/'+jsmap.OUT_NAME_MAP)
async def get_out_js_map(request: web.Request):
    return web.Response(body=jsmap.cache.map, content_type='application/json')


routes.static('/css', config.BASE_PATH / 'css')
routes.static('/js', config.JS_PATH)

async def startup(app):
    if config.WORKER_SERVER.run_with_web:
        if not config.PRODUCTIVE:
            from pantra.watchers import start_observer
            start_observer()
        asyncio.create_task(Session.run_server_worker())

async def web_app():
    global bootstrap
    if not config.BOOTSTRAP_FILENAME.exists():
        print(f'File `{config.BOOTSTRAP_FILENAME}` not found')
        sys.exit(1)

    bootstrap = config.BOOTSTRAP_FILENAME.read_text()

    # patch incorrect default python mime-types
    mimetypes.init()
    mimetypes.add_type('application/javascript', '.js')

    app = web.Application()

    if config.WEB_PATH:
        from aiohttp.web_routedef import RouteDef, StaticDef
        for route in routes:
            if type(route) is RouteDef:
                app.router.add_route(route.method, config.WEB_PATH + route.path, route.handler, **route.kwargs)
            elif type(route) is StaticDef:
                app.router.add_static(config.WEB_PATH + route.prefix, route.path, **route.kwargs)
            else:
                raise "Call a coder here"
    else:
        app.add_routes(routes)

    app.on_startup.append(startup)

    return app


async def main(host, port):
    app = await web_app()

    #web.run_app(app, port=8005)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port, shutdown_timeout=0)
    await site.start()
    # wait for finish signal
    print(f'Running wild at {host}:{port}')
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


def run(host=None, port=8005):
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(host, port))


if __name__ == '__main__':
    run()
