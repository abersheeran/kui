import os
import sys
import json
import logging
import importlib

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException

from .config import Config
from .autoreload import MonitorFile, checkall

logger = logging.getLogger(__name__)
config = Config()

sys.path.insert(0, config.path)

app = Starlette(debug=config.DEBUG)

# middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.ALLOWED_HOSTS
)
if config.FORCE_SSL:
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_SETTINGS.ALLOW_ORIGINS,
    allow_methods=config.CORS_SETTINGS.ALLOW_METHODS,
    allow_headers=config.CORS_SETTINGS.ALLOW_HEADERS,
    allow_credentials=config.CORS_SETTINGS.ALLOW_CREDENTIALS,
    allow_origin_regex=config.CORS_SETTINGS.ALLOW_ORIGIN_REGEX,
    expose_headers=config.CORS_SETTINGS.EXPOSE_HEADERS,
    max_age=config.CORS_SETTINGS.MAX_AGE,
)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024
)

monitor: MonitorFile = None


@app.on_event('startup')
async def startup():
    # check import
    for _path_ in os.listdir(config.path):
        if _path_ in ("statics", "templates"):
            continue
        checkall(_path_)

    # monitor file event
    global monitor
    monitor = MonitorFile(config.path)

    # static & template
    os.makedirs(os.path.join(config.path, "statics"), exist_ok=True)
    os.makedirs(os.path.join(config.path, "templates"), exist_ok=True)
    app.mount('/static', StaticFiles(directory="statics"))


@app.on_event('shutdown')
async def shutdown():
    global monitor
    monitor.stop()


@app.route("/")
async def index(request):
    request.path_params['filepath'] = ""
    return await http(request)


@app.route('/favicon.ico')
async def favicon(request):
    return RedirectResponse("/static/favicon.ico")


@app.route("/{filepath:path}", methods=['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'])
async def http(request):
    filepath = request.path_params['filepath']
    if filepath == "" or filepath.endswith("/"):
        filepath += "index"
    # Google SEO
    if not config.ALLOW_UNDERLINE:
        if "_" in filepath:
            return RedirectResponse(f'/{filepath.replace("_", "-")}', status_code=301)
        filepath = filepath.strip(".").replace("-", "_")

    # judge python file
    abspath = os.path.join(config.path, "views", filepath + ".py")
    if not os.path.exists(abspath):
        raise HTTPException(404)

    pathlist = ['views'] + filepath.split("/")

    # find http handler
    module_path = ".".join(pathlist)
    module = importlib.import_module(module_path)
    try:
        get_response = module.HTTP()
    except AttributeError:
        raise HTTPException(404)

    # call middleware
    for deep in range(len(pathlist), 0, -1):
        try:
            module = importlib.import_module(".".join(pathlist[:deep]))
            get_response = module.Middleware(get_response)
            logger.debug(f"Call middleware in {module}")
        except AttributeError:
            continue

    # get response
    return await get_response(request)
