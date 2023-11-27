import asyncio
import sys
import traceback
import mimetypes
import logging

import sass
from aiohttp import web, WSMessage, WSMsgType, streamer

from .components.context import HTMLElement
from .components.controllers import process_click, process_drag_start, process_drag_move, process_drag_stop, \
    process_select, process_bind_value, process_key, process_direct_call
from .components.loader import collect_styles, templates
from .serializer import serializer
from .settings import config
from .patching import wipe_logger
from .session import Session
from .workers import start_task_workers, init_async_worker, stop_task_workers, thread_worker
from .watchers import start_observer, stop_observer
from .compiler import code_base
from .oid import get_node
from . import jsmap

__all__ = ['run']

routes = web.RouteTableDef()
logger = logging.getLogger('pantra.system')


@routes.get(r'/{app:\w*}')
@wipe_logger
async def get_main_page(request: web.Request):
    local_id = Session.gen_session_id()
    session_id = Session.gen_session_id()
    body = bootstrap.replace('{{LOCAL_ID}}', local_id)
    body = body.replace('{{TAB_ID}}', session_id)
    body = body.replace('{{WEB_PATH}}', config.WEB_PATH)
    logger.debug(f"Bootstrap page rendered {local_id}/{session_id}")
    return web.Response(body=body, content_type='text/html')


@streamer
async def file_sender(writer, file_path=None):
    with open(file_path, 'rb') as f:
        chunk = f.read(2 ** 16)
        while chunk:
            await writer.write(chunk)
            chunk = f.read(2 ** 16)


@routes.get(r'/{app:\w*}/m/{file:.+}')
async def get_media(request: web.Request):
    app = request.match_info['app']
    if not app:
        file_path = config.COMPONENTS_PATH if config.DEFAULT_APP == 'Core' else config.APPS_PATH / config.DEFAULT_APP
    else:
        file_path = config.APPS_PATH / app
    file_path /= request.match_info['file']
    if not file_path.exists():
        return web.Response(body=f'File `{file_path.name}` not found', status=404)
    headers = {
        "Content-disposition": f"attachment; filename={file_path.name}",
        "Content-type": mimetypes.guess_type(file_path)[0],
    }
    return web.Response(body=file_sender(file_path=str(file_path)), headers=headers)


@routes.get(r'/{app:\w*}/ws/{local_id:\w+}/{session_id:\w+}')
@wipe_logger
async def get_ws(request: web.Request):
    ws = web.WebSocketResponse(receive_timeout=config.SOCKET_TIMEOUT, max_msg_size=config.MAX_MESSAGE_SIZE)
    await ws.prepare(request)

    app = request.match_info['app']
    if not app:
        app = config.DEFAULT_APP

    logger.debug(f"WebSocket connected {{{app}}} {request.match_info['local_id']}/{request.match_info['session_id']}")

    lang_info = request.headers.get('Accept-Language', 'en')
    lang = [part.split(';')[0].replace('-', '_') for part in lang_info.split(',')]
    session = Session(request.match_info['local_id'], request.match_info['session_id'], ws, app, lang)

    # token = request.match_info['token']

    try:
        async for msg in ws:  # type WSMessage
            if msg.type == WSMsgType.BINARY:
                data = serializer.decode(msg.data)
                command = data['C']
                if command in ('REFRESH', 'UP'):
                    if session.just_connected:
                        session.just_connected = False
                        @thread_worker
                        def restart():
                            session.restart()
                        restart()
                    else:
                        if command == 'REFRESH':
                            logger.debug("[REFRESH] command")
                            if hasattr(session.state, 'drag'):
                                process_drag_stop(session, 0, 0)
                            await session.send_root()
                            if session.title:
                                await session.send_title(session.title)
                        await session.recover_messages()
                        await session.remind_errors()

                elif command == 'CLICK':
                    logger.debug(f"[CLICK] command `{data['method']}` to <{getattr(get_node(data['oid']), 'context', 'none')}>")
                    process_click(data['method'], data['oid'])

                elif command == 'SELECT':
                    logger.debug(f"[SELECT] command `{data['method']}` to <{getattr(get_node(data['oid']), 'context', 'none')}>")
                    process_select(data['method'], data['oid'], data['opts'])

                elif command == 'KEY':
                    logger.debug(f"[KEY] command `{data['method']}` - `{data['key']}` to <{getattr(get_node(data['oid']), 'context', 'none')}>")
                    process_key(data['method'], data['oid'], data['key'])

                elif command == 'B':
                    logger.debug("[B]ind value command")
                    process_bind_value(data['oid'], data['v'], data['x'])

                elif command == 'M':
                    logger.debug(f"[M]etrics received for <{get_node(data['oid'])}>")
                    HTMLElement._set_metrics(data['oid'], data)

                elif command == 'V':
                    logger.debug(f"[V]alue received for <{get_node(data['oid'])}>")
                    HTMLElement._set_value(data['oid'], data['value'])

                elif command == 'DD':
                    logger.debug(f"[DD]rag Start `{data['method']}` for <{get_node(data['oid'])}>")
                    process_drag_start(session, data['method'], data['oid'], data['x'], data['y'], data['button'])

                elif command == 'DM':
                    logger.debug("[D]rag [M]ove")
                    process_drag_move(session, data['x'], data['y'])

                elif command == 'DU':
                    logger.debug("[D]rag [S]top")
                    process_drag_stop(session, data['x'], data['y'])

                elif command == 'VALID':
                    logger.debug(f"[VALID]ity received for <{get_node(data['oid'])}>")
                    HTMLElement._set_validity(data['oid'], data['validity'])

                elif command == 'CALL':
                    logger.debug(f"[CALL] command `{data['method']}` to  <{getattr(get_node(data['oid']), 'context', 'none')}>")
                    process_direct_call(data['oid'], data['method'], data['args'])

            elif msg.type == WSMsgType.ERROR:
                logger.error(f'WebSocket connection closed with exception {ws.exception()}')
    except asyncio.exceptions.TimeoutError:
        pass
    except asyncio.exceptions.CancelledError:
        raise
    except:
        logger.error(f"WebSocket error: {traceback.format_exc(-1)}")
        session.ws = None
        await session.send_message({'m': 'e', 'l': traceback.format_exc()})
    session.ws = None

    return ws


# TODO: cache styles and join with file watcher
@routes.get(r'/css/global.css')
@wipe_logger
async def get_global_css(request: web.Request):
    logger.debug("Collecting global components` styles")
    styles = collect_styles(config.COMPONENTS_PATH, Session.error_later)
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
    styles = collect_styles(app_path, Session.error_later)
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
async def get_out_js(request: web.Request):
    return web.Response(body=jsmap.cache.map, content_type='application/javascript', headers={'SourceMap': jsmap.OUT_NAME+'.map'})


routes.static('/css', config.BASE_PATH / 'css', append_version=True)
routes.static('/js', config.JS_PATH)

async def startup(app):
    start_task_workers()
    init_async_worker()
    start_observer(templates, Session, code_base)


async def shutdown(app):
    stop_task_workers()
    stop_observer()


async def web_app():
    global bootstrap
    if not config.BOOTSTRAP_FILENAME.exists():
        print(f'File `{config.BOOTSTRAP_FILENAME}` not found')
        sys.exit(1)

    bootstrap = config.BOOTSTRAP_FILENAME.read_text()

    # patch incorrect default python mime-types
    mimetypes.init()
    mimetypes.add_type('application/javascript', '.js')

    if config.ENABLE_LOGGING:
        setup_logger()

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

    #app.add_routes(routes)

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)

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


def setup_logger(level: int = logging.DEBUG):
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.debug("Logger configured")


def run(host=None, port=8005):
    asyncio.run(main(host, port))


if __name__ == '__main__':
    run()
