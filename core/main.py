import asyncio
import sys
from typing import *

import sass
from aiohttp import web, WSMessage, WSMsgType
from aiohttp.web_request import Request

from core.components.context import Context, HTMLElement
from core.components.controllers import process_click, process_drag_start, process_drag_move, process_drag_stop, \
    process_select
import core.database as db
from core.components.loader import collect_styles
from core.components.render import ContextShot
from core.serializer import serializer
from core.defaults import *
from core.session import Session
from core.workers import start_task_workers, init_async_worker, stop_task_workers, thread_worker
from tracker import start_observer, stop_observer

routes = web.RouteTableDef()


@routes.get(r'/{app:\w*}')
async def get_main_page(request: Request):
    body = bootstrap.replace('{{hostname}}', f'{request.host}/{request.match_info["app"]}')
    body = body.replace('{{session_id}}', Session.gen_session_id())
    body = body.replace('{{app}}', request.match_info["app"])
    return web.Response(body=body, content_type='text/html')


@routes.get(r'/{app:\w*}/ws/{session_id:\w+}')
async def get_ws(request: Request):
    ws = web.WebSocketResponse(receive_timeout=SOCKET_TIMEOUT)
    await ws.prepare(request)

    app = request.match_info['app']
    if app:
        app = os.path.join(APPS_PATH, app)
    else:
        app = COMPONENTS_PATH
    session = Session(request.match_info['session_id'], ws, app)

    # token = request.match_info['token']
    ctx: Optional[Context] = None

    try:
        async for msg in ws:  # type: WSMessage
            if msg.type == WSMsgType.BINARY:
                data = serializer.decode(msg.data)
                command = data['C']
                if command == 'REFRESH':
                    if session.just_connected:
                        session.just_connected = False
                        shot = ContextShot()
                        await session.remind_errors()
                        await session.send_message({'m': 'rst'})

                        @thread_worker
                        def build_root():
                            ctx.render.build()
                            session.root = ctx
                            session.send_shot(shot)

                        ctx = Context("Main", shot=shot, session=session)
                        build_root()
                    else:
                        ctx = session.root
                        await session.recover_messages()

                elif command == 'CLICK':
                    process_click(data['method'], int(data['oid']))

                elif command == 'SELECT':
                    process_select(data['method'], int(data['oid']), data['opts'])

                elif command == 'M':
                    HTMLElement._set_metrics(int(data['oid']), data)

                elif command == 'V':
                    HTMLElement._set_value(int(data['oid']), data['value'])

                elif command == 'DD':
                    process_drag_start(ctx, data['method'], int(data['oid']), data['x'], data['y'], data['button'])

                elif command == 'DM':
                    process_drag_move(ctx, data['x'], data['y'])

                elif command == 'DU':
                    process_drag_stop(ctx, data['x'], data['y'])

                #await send_shot()
                #print(f'message processed {command}')

            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
    except TimeoutError:
        pass
    except Exception as e:
        session.ws = None
        await session.send_message({'m': 'e', 'l': str(e)})
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
    start_observer()


async def shutdown(app):
    stop_task_workers()
    stop_observer()


async def main():
    app = web.Application()
    app.add_routes(routes)

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)

    #web.run_app(app, port=8005)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8005)
    await site.start()
    # wait for finish signal
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    if not os.path.exists(os.path.join(COMPONENTS_PATH, 'bootstrap.html')):
        print('File <bootstrap.html> not found')
        sys.exit(1)

    with open(os.path.join(COMPONENTS_PATH, 'bootstrap.html'), 'rt') as f:
        bootstrap = f.read()

    asyncio.run(main())
