import asyncio
import sys
from typing import *

import sass
from aiohttp import web, WSMessage, WSMsgType
from aiohttp.web_request import Request

from core.components.context import Context
from core.components.controllers import process_click, process_drag_start, process_drag_move, process_drag_stop
from core.components.htmlnode import collect_styles
import core.database as db
from core.components.render import ContextShot, RenderMixin
from core.serializer import serializer
from core.defaults import *
from core.session import Session
from core.workers import start_task_workers, init_async_worker, stop_task_workers

routes = web.RouteTableDef()


@routes.get(r'/{app:\w*}')
async def get_main_page(request: Request):
    body = template.replace('{{hostname}}', f'{request.host}/{request.match_info["app"]}')
    body = body.replace('{{session_id}}', Session.gen_session_id())
    return web.Response(body=body, content_type='text/html')


@routes.get(r'/{app:\w*}/ws/{session_id:\w+}')
async def get_ws(request: Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    app = request.match_info['app']
    if app:
        app = os.path.join(APPS_PATH, app)
    else:
        app = COMPONENTS_PATH
    session = Session(request.match_info['session_id'], ws, app)

    async def send_message(message: Dict):
        await ws.send_bytes(serializer.encode(message))

    # token = request.match_info['token']
    ctx: Optional[Context] = None
    shot: Optional[ContextShot] = None

    async for msg in ws:  # type: WSMessage
        if msg.type == WSMsgType.BINARY:
            data = serializer.decode(msg.data)
            command = data['C']
            if command == 'RESTART':
                shot = ContextShot()
                ctx = Context("Main", shot=shot, session=session)
                ctx.render.build()
                session.root = ctx
                await session.send_message({'m': 'u', 'l': shot.rendered})

            elif command == 'CLICK':
                process_click(data['method'], int(data['oid']))

            elif command == 'M':
                RenderMixin._set_metrics(int(data['oid']), data)

            elif command == 'V':
                RenderMixin._set_value(int(data['oid']), data['value'])

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

    print('websocket connection closed')

    return ws


@routes.get(r'/css/global.css')
async def get_global_css(request: Request):
    styles = collect_styles()
    return web.Response(body=styles, content_type='text/css')


@routes.get(r'/css/{name:.+?}.scss')
async def get_static_scss(request: Request):
    try:
        file_name = os.path.join(CSS_PATH, request.match_info['name'])
        with open(file_name+'.scss', "rt", encoding='utf-8') as f:
            text = f.read()
        css = sass.compile(string=text, output_style='compact', include_paths=[CSS_PATH])
    except:
        return web.Response(status=404)
    else:
        return web.Response(body=css, content_type='text/css')

routes.static('/js', os.path.join(BASE_PATH, 'js'))
routes.static('/css', os.path.join(BASE_PATH, 'css'))


async def startup(app):
    db.connect()
    start_task_workers()
    init_async_worker()


async def shutdown(app):
    stop_task_workers()


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
    if not os.path.exists(os.path.join(PAGES_PATH, 'page.html')):
        print('File <page.html> not found')
        sys.exit(1)

    with open(os.path.join(PAGES_PATH, 'page.html'), 'rt', encoding='utf-8-sig') as f:
        template = f.read()

    asyncio.run(main())
