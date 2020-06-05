import asyncio
import sys
import traceback
from concurrent.futures import TimeoutError

import sass
from aiohttp import web, WSMessage, WSMsgType
from aiohttp.web_request import Request
from aiohttp_session import setup, SimpleCookieStorage, get_session

from core.components.context import HTMLElement
from core.components.controllers import process_click, process_drag_start, process_drag_move, process_drag_stop, \
    process_select, process_bind_value, process_key
import core.database as db
from core.components.loader import collect_styles, templates
from core.serializer import serializer
from core.defaults import *
from core.session import Session
from core.workers import start_task_workers, init_async_worker, stop_task_workers, thread_worker
from core.tracker import start_observer, stop_observer
from core.compiler import code_base


routes = web.RouteTableDef()


@routes.get(r'/{app:\w*}')
async def get_main_page(request: Request):
    session = await get_session(request)
    body = bootstrap.replace('{{hostname}}', f'{request.host}/{request.match_info["app"]}')
    session_id = session.get('id')
    if not session_id:
        session_id = Session.gen_session_id()
        session['id'] = session_id
    body = body.replace('{{session_id}}', session_id)
    body = body.replace('{{app}}', request.match_info["app"])
    return web.Response(body=body, content_type='text/html')


@routes.get(r'/{app:\w*}/ws/{session_id:\w+}')
async def get_ws(request: Request):
    ws = web.WebSocketResponse(receive_timeout=SOCKET_TIMEOUT, max_msg_size=MAX_MESSAGE_SIZE)
    await ws.prepare(request)

    app = request.match_info['app']
    if app:
        app = os.path.join(APPS_PATH, app)
    else:
        app = COMPONENTS_PATH
    session = Session(request.match_info['session_id'], ws, app)

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
                            await session.send_root()
                            if session.title:
                                await session.send_title(session.title)
                        await session.recover_messages()

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

                elif command == 'DM':
                    process_drag_move(session, data['x'], data['y'])

                elif command == 'DU':
                    process_drag_stop(session, data['x'], data['y'])

                #await send_shot()
                #print(f'message processed {command}')

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

routes.static('/js', os.path.join(BASE_PATH, 'js'), append_version=True)
routes.static('/css', os.path.join(BASE_PATH, 'css'), append_version=True)


async def startup(app):
    db.connect()
    start_task_workers()
    init_async_worker()
    start_observer(templates, Session, code_base)


async def shutdown(app):
    stop_task_workers()
    stop_observer()


async def main():
    app = web.Application()
    app.add_routes(routes)

    setup(app, SimpleCookieStorage(cookie_name='s'))

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)

    #web.run_app(app, port=8005)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8005)
    await site.start()
    # wait for finish signal
    print('Running wild at 8005')
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


def run():
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

    asyncio.run(main())


if __name__ == '__main__':
    run()
