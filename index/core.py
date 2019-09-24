import os
import sys
import logging

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .config import config
from .autoreload import MonitorFile
from .application import Index

logger = logging.getLogger(__name__)

sys.path.insert(0, config.path)

app = Index(debug=config.DEBUG)

# middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_origin_regex=config.CORS_ALLOW_ORIGIN_REGEX,
    expose_headers=config.CORS_EXPOSE_HEADERS,
    max_age=config.CORS_MAX_AGE,
)

if config.FORCE_SSL:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.ALLOWED_HOSTS
)


monitor: MonitorFile = None


@app.on_event('startup')
async def check_on_startup() -> None:
    # monitor file event
    global monitor
    monitor = MonitorFile(config.path)


@app.on_event('shutdown')
async def clear_check_on_shutdown() -> None:
    global monitor
    monitor.stop()


@app.on_event('startup')
async def create_directories() -> None:
    """
    create directories for static & template
    """
    os.makedirs(os.path.join(config.path, "static"), exist_ok=True)
    os.makedirs(os.path.join(config.path, "templates"), exist_ok=True)
