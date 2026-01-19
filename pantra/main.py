import typing
import asyncio
import os
import mimetypes
import logging

from starlette.applications import Starlette
from starlette.routing import Mount

from pantra.settings import config

__all__ = ['run']

logger = logging.getLogger('pantra.system')

def web_app(args):
    # patch incorrect default python mime-types
    mimetypes.init()
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('application/x-yaml', '.yaml')
    mimetypes.add_type('application/x-yaml', '.yml')

    router = config.ROUTER_CLASS()
    if config.WEB_PATH:
        routes = [Mount(config.WEB_PATH, routes=router.routes())]
    else:
        routes = router.routes()
    app = Starlette(debug=not config.PRODUCTIVE, routes=routes, on_startup=[router.startup])
    return app


def run(host=None, port=8005):
    import uvicorn

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(
        web_app(None),
        host=host,
        port=port,
        ws_ping_interval=config.WS_HEARTBEAT_INTERVAL,
        ws_ping_timeout=config.SOCKET_TIMEOUT,
    )


if __name__ == '__main__':
    run()
