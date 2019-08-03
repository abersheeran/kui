import os
import sys
import json
import importlib

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from .config import Config, logger
from .responses import automatic
from .watchdog import MonitorFile

config = Config()

sys.path.insert(0, config.path)

app = Starlette(debug=config.DEBUG)

# middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.ALLOWED_HOSTS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_SETTINGS.allow_origins,
    allow_methods=config.CORS_SETTINGS.allow_methods,
    allow_headers=config.CORS_SETTINGS.allow_headers,
    allow_credentials=config.CORS_SETTINGS.allow_credentials,
    allow_origin_regex=config.CORS_SETTINGS.allow_origin_regex,
    expose_headers=config.CORS_SETTINGS.expose_headers,
    max_age=config.CORS_SETTINGS.max_age,
)

# monitor file event
monitorfile = MonitorFile()

# static & template
os.makedirs(os.path.join(config.path, "statics"), exist_ok=True)
os.makedirs(os.path.join(config.path, "templates"), exist_ok=True)

app.mount('/static', StaticFiles(directory="statics"))


@app.route("/")
def index(request):
    return RedirectResponse("/index.py", status_code=301)


@app.route('/favicon.ico')
def favicon(request):
    return RedirectResponse("/static/favicon.ico")


@app.route("/{filepath:path}.py", methods=['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'])
async def http(request):
    filepath = request.path_params['filepath']
    # Google SEO
    if not config.ALLOW_UNDERLINE:
        if "_" in filepath:
            return RedirectResponse(f'/{filepath.replace("_", "-")}.py', status_code=301)
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
    resp = await get_response(request)
    if not isinstance(resp, tuple):
        resp = (resp,)
    return automatic(*resp)
