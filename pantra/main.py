import asyncio
import os

from starlette.applications import Starlette
from starlette.routing import Mount

from pantra.settings import config

__all__ = ['run']

def web_app():
    router = config.ROUTER_CLASS()
    if config.WEB_PATH:
        routes = [Mount(config.WEB_PATH, routes=router.routes())]
    else:
        routes = router.routes()
    app = Starlette(debug=not config.PRODUCTIVE,
                    routes=routes,
                    on_startup=[router.startup],
                    on_shutdown=[router.shutdown])
    return app

def run(host=None, port=8005):
    import uvicorn

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(
        web_app(),
        host=host,
        port=port,
        ws_ping_interval=config.WS_HEARTBEAT_INTERVAL,
        ws_ping_timeout=config.SOCKET_TIMEOUT,
    )


if __name__ == '__main__':
    run()
