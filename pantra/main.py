import asyncio
import sys
import traceback
import mimetypes

import sass
from aiohttp import web, WSMessage, WSMsgType, streamer

from .components.context import HTMLElement
from .components.controllers import process_click, process_drag_start, process_drag_move, process_drag_stop, \
    process_select, process_bind_value, process_key, process_direct_call
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
async def get_main_page(request: web.Request):
    body = bootstrap.replace('{{LOCAL_ID}}', Session.gen_session_id())
    body = body.replace('{{TAB_ID}}', Session.gen_session_id())
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
        file_path = COMPONENTS_PATH
    else:
        file_path = APPS_PATH / app
    file_path /= request.match_info['file']
    if not file_path.exists():
        return web.Response(body=f'File `{file_path.name}` not found', status=404)
    headers = {
        "Content-disposition": f"attachment; filename={file_path.name}",
        "Content-type": mimetypes.guess_type(file_path)[0],
    }
    return web.Response(body=file_sender(file_path=str(file_path)), headers=headers)


@routes.get(r'/{app:\w*}/ws/{local_id:\w+}/{session_id:\w+}')
async def get_ws(request: web.Request):
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

                elif command == 'DM':
                    process_drag_move(session, data['x'], data['y'])

                elif command == 'DU':
                    process_drag_stop(session, data['x'], data['y'])

                elif command == 'VALID':
                    HTMLElement._set_validity(data['oid'], data['validity'])

                elif command == 'CALL':
                    process_direct_call(data['oid'], data['method'], data['args'])

            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
    except asyncio.exceptions.TimeoutError:
        pass
    except asyncio.exceptions.CancelledError:
        raise
    except:
        session.ws = None
        await session.send_message({'m': 'e', 'l': traceback.format_exc()})
    session.ws = None

    return ws


# TODO: cache styles and join with file watcher
@routes.get(r'/css/global.css')
async def get_global_css(request: web.Request):
    styles = collect_styles(COMPONENTS_PATH, Session.error_later)
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{app:\w*}.local.css')
async def get_local_css(request: web.Request):
    app = request.match_info['app']
    if not app:
        return web.Response(content_type='text/css')
    app_path = APPS_PATH / app
    styles = collect_styles(app_path, Session.error_later)
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{name:.+?}.scss')
async def get_static_scss(request: web.Request):
    file_name = request.match_info['name']
    try:
        file_name = CSS_PATH / file_name
        text = file_name.with_suffix('.scss').read_text(encoding='utf-8')
        css = sass.compile(string=text, output_style='compact', include_paths=[str(CSS_PATH)])
    except Exception as e:
        Session.error_later(f'{file_name}.scss> {e}')
        return web.Response(status=404)
    else:
        return web.Response(body=css, content_type='text/css')


@routes.get(r'/js/'+jsmap.OUT_NAME)
async def get_out_js(request: web.Request):
    jsmap.make(JS_PATH)  # TODO: Cache it!
    file_name = JS_PATH / jsmap.OUT_NAME
    text = file_name.read_text('utf-8')
    return web.Response(body=text, content_type='application/javascript', headers={'SourceMap': jsmap.OUT_NAME+'.map'})


routes.static('/js', BASE_PATH / 'js', append_version=True)
routes.static('/css', BASE_PATH / 'css', append_version=True)


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
    global bootstrap
    if not (COMPONENTS_PATH / 'bootstrap.html').exists():
        print('File <bootstrap.html> not found')
        sys.exit(1)

    bootstrap = (COMPONENTS_PATH / 'bootstrap.html').read_text()

    # patch incorrect default python mime-types
    mimetypes.init()
    mimetypes.add_type('application/javascript', '.js')

    asyncio.run(main(host, port))


if __name__ == '__main__':
    run()
