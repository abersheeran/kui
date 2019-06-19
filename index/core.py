import os
import sys
import json
import importlib

import uvicorn
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.responses import Response, RedirectResponse

from .config import Config, logger
from .responses import automatic
from .errors import Http404, Http500

config = Config()

sys.path.insert(0, config.path)

app = Starlette(debug=config.DEBUG)

os.makedirs(os.path.join(config.path, "statics"), exist_ok=True)
os.makedirs(os.path.join(config.path, "templates"), exist_ok=True)

templates = Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory="statics"))


@app.route("/")
def index(request):
    return RedirectResponse("/home.py", status_code=301)


@app.route('/favicon.ico')
def favicon(request):
    return RedirectResponse("/static/favicon.ico")


@app.route("/{filepath:path}.py", methods=['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'])
def http(request):
    filepath = request.path_params['filepath']
    # Google SEO
    if "_" in filepath:
        return RedirectResponse(filepath.replace("_", "-"), status_code=301)

    filepath = filepath.strip(".").replace("-", "_")
    # judge python file
    abspath = os.path.join(config.path, filepath + ".py")
    if not os.path.exists(abspath):
        raise Http404()

    module_path = ".".join(filepath.split("/"))
    module = importlib.import_module(module_path)
    try:
        if module.AUTORELOAD:
            importlib.reload(module)
    except AttributeError:
        module.AUTORELOAD = True

    try:
        resp = module.HTTP(request).dispatch()
    except AttributeError:
        raise Http404()

    if not isinstance(resp, tuple):
        resp = (resp,)
    return automatic(*resp)


def main():
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        debug=config.DEBUG,
        logger=logger
    )
