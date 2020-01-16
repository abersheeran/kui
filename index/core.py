import os
import sys
import logging
from typing import Optional

from starlette.staticfiles import StaticFiles
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.exceptions import ExceptionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from .config import config
from .autoreload import MonitorFile
from .applications import Index, favicon

logger = logging.getLogger(__name__)

sys.path.insert(0, config.path)

app = Index(debug=config.DEBUG)

app.mount("/favicon.ico", favicon, "asgi")
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(config.path, "static"), check_dir=False),
    "asgi",
)

if config.FORCE_SSL:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)

if config.HOTRELOAD:
    monitor: Optional[MonitorFile] = None

    @app.on_event("startup")
    async def check_on_startup() -> None:
        # monitor file event
        global monitor
        monitor = MonitorFile(config.path)

    @app.on_event("shutdown")
    async def clear_check_on_shutdown() -> None:
        global monitor
        if monitor is not None:
            monitor.stop()


@app.on_event("startup")
async def create_directories() -> None:
    """
    create directories for static & template
    """
    os.makedirs(os.path.join(config.path, "views"), exist_ok=True)
    os.makedirs(os.path.join(config.path, "static"), exist_ok=True)
    os.makedirs(os.path.join(config.path, "templates"), exist_ok=True)
