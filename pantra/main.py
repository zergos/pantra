import asyncio
import sys
import traceback
from concurrent.futures import TimeoutError

import sass
from aiohttp import web, WSMessage, WSMsgType
from aiohttp.web_request import Request
from aiohttp_session import setup, SimpleCookieStorage, get_session

from .components.context import HTMLElement
from .components.controllers import process_click, process_drag_start, process_drag_move, process_drag_stop, \
    process_select, process_bind_value, process_key
from .components.loader import collect_styles, templates
from .serializer import serializer
from .defaults import *
from .session import Session
from .workers import start_task_workers, init_async_worker, stop_task_workers, thread_worker
from .watchers import start_observer, stop_observer
from .compiler import code_base
from . import jsmap

__all__ = ['run']

routes = web.RouteTableDef()


@routes.get(r'/{app:\w*}')
async def get_main_page(request: Request):
    body = bootstrap.replace('{{LOCAL_ID}}', Session.gen_session_id())
    body = body.replace('{{TAB_ID}}', Session.gen_session_id())
    return web.Response(body=body, content_type='text/html')


@routes.get(r'/{app:\w*}/ws/{local_id:\w+}/{session_id:\w+}')
async def get_ws(request: Request):
    ws = web.WebSocketResponse(receive_timeout=SOCKET_TIMEOUT, max_msg_size=MAX_MESSAGE_SIZE)
    await ws.prepare(request)

    app = request.match_info['app']
    if not app:
        app = 'Core'

    lang_info = request.headers.get('Accept-Language', 'en')
    lang = [part.split(';')[0].replace('-', '_') for part in lang_info.split(',')]
    session = Session(request.match_info['session_id'], ws, app, lang)

    # token = request.match_info['token']

    try:
        async for msg in ws:  # type: WSMessage
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
                            if hasattr(session.state, 'drag'):
                                process_drag_stop(session, 0, 0)
                            await session.send_root()
                            if session.title:
                                await session.send_title(session.title)
                        await session.recover_messages()
                        await session.remind_errors()

                elif command == 'CLICK':
                    process_click(data['method'], data['oid'])

                elif command == 'SELECT':
                    process_select(data['method'], data['oid'], data['opts'])

                elif command == 'KEY':
                    process_key(data['method'], data['oid'], data['key'])

                elif command == 'B':
                    process_bind_value(data['oid'], data['v'], data['x'])

                elif command == 'M':
                    HTMLElement._set_metrics(data['oid'], data)

                elif command == 'V':
                    HTMLElement._set_value(data['oid'], data['value'])

                elif command == 'DD':
                    process_drag_start(session, data['method'], data['oid'], data['x'], data['y'], data['button'])
                    #print('DD')

                elif command == 'DM':
                    process_drag_move(session, data['x'], data['y'])

                elif command == 'DU':
                    process_drag_stop(session, data['x'], data['y'])
                    #print('DU')

                elif command == 'VALID':
                    HTMLElement._set_validity(data['oid'], data['validity'])

            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
    except TimeoutError:
        pass
    except Exception as e:
        session.ws = None
        await session.send_message({'m': 'e', 'l': traceback.format_exc()})
    session.ws = None

    return ws


# TODO: cache styles and join with file watcher
@routes.get(r'/css/global.css')
async def get_global_css(request: Request):
    styles = collect_styles(COMPONENTS_PATH, Session.error_later)
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{app:\w*}.local.css')
async def get_local_css(request: Request):
    app = request.match_info['app']
    if not app:
        return web.Response(content_type='text/css')
    app_path = os.path.join(APPS_PATH, app)
    styles = collect_styles(app_path, Session.error_later)
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{name:.+?}.scss')
async def get_static_scss(request: Request):
    file_name = request.match_info['name']
    try:
        file_name = os.path.join(CSS_PATH, file_name)
        with open(file_name+'.scss', "rt", encoding='utf-8') as f:
            text = f.read()
        css = sass.compile(string=text, output_style='compact', include_paths=[CSS_PATH])
    except Exception as e:
        Session.error_later(f'{file_name}.scss> {e}')
        return web.Response(status=404)
    else:
        return web.Response(body=css, content_type='text/css')


@routes.get(r'/js/'+jsmap.OUT_NAME)
async def get_out_js(request: Request):
    jsmap.make(JS_PATH)  # TODO: Cache it!
    file_name = os.path.join(JS_PATH, jsmap.OUT_NAME)
    with open(file_name, "rt", encoding='utf-8') as f:
        text = f.read()
    return web.Response(body=text, content_type='application/javascript', headers={'SourceMap': jsmap.OUT_NAME+'.map'})


routes.static('/js', os.path.join(BASE_PATH, 'js'), append_version=True)
routes.static('/css', os.path.join(BASE_PATH, 'css'), append_version=True)


async def startup(app):
    start_task_workers()
    init_async_worker()
    start_observer(templates, Session, code_base)


async def shutdown(app):
    stop_task_workers()
    stop_observer()


async def main(host, port):
    app = web.Application()
    app.add_routes(routes)

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)

    #web.run_app(app, port=8005)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    # wait for finish signal
    print(f'Running wild at {host}:{port}')
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


def run(host=None, port=8005):
    global bootstrap
    if not os.path.exists(os.path.join(COMPONENTS_PATH, 'bootstrap.html')):
        print('File <bootstrap.html> not found')
        sys.exit(1)

    with open(os.path.join(COMPONENTS_PATH, 'bootstrap.html'), 'rt') as f:
        bootstrap = f.read()

    # patch incorrect default python mime-types
    import mimetypes
    mimetypes.init()
    mimetypes.add_type('application/javascript', '.js')

    asyncio.run(main(host, port))


if __name__ == '__main__':
    run()
